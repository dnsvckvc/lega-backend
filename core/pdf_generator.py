from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
from datetime import date
from decimal import Decimal


class InvoicePDFGenerator:
    """Generate professional PDF invoices using reportlab"""
    
    def __init__(self, company_info=None):
        self.company_info = company_info or self._get_default_company_info()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _get_default_company_info(self):
        """Default company information - should be configurable in production"""
        return {
            'name': 'Legal Practice Management',
            'address': '123 Legal Street\nLaw City, LC 12345',
            'phone': '+1 (555) 123-4567',
            'email': 'billing@legalpractice.com',
            'website': 'www.legalpractice.com',
            'tax_id': 'TAX-123456789'
        }
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the invoice"""
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#e74c3c'),
            spaceAfter=20,
            alignment=TA_RIGHT
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=16
        ))
        
        self.styles.add(ParagraphStyle(
            name='Address',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=4
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
    
    def generate_invoice_pdf(self, invoice):
        """
        Generate PDF for an invoice
        
        Args:
            invoice: Invoice model instance
            
        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Header section
        story.extend(self._build_header(invoice))
        story.append(Spacer(1, 24))
        
        # Invoice info and client info
        story.extend(self._build_invoice_info(invoice))
        story.append(Spacer(1, 24))
        
        # Line items table
        story.extend(self._build_line_items_table(invoice))
        story.append(Spacer(1, 24))
        
        # Totals section
        story.extend(self._build_totals_section(invoice))
        story.append(Spacer(1, 24))
        
        # Notes and payment terms
        if invoice.notes:
            story.extend(self._build_notes_section(invoice))
        
        story.extend(self._build_payment_terms())
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _build_header(self, invoice):
        """Build the invoice header with company info"""
        elements = []
        
        # Create header table with company info and invoice title
        header_data = [
            [
                Paragraph(self.company_info['name'], self.styles['CompanyName']),
                Paragraph('INVOICE', self.styles['InvoiceTitle'])
            ],
            [
                Paragraph(
                    f"{self.company_info['address']}<br/>"
                    f"Phone: {self.company_info['phone']}<br/>"
                    f"Email: {self.company_info['email']}<br/>"
                    f"Web: {self.company_info['website']}",
                    self.styles['Address']
                ),
                ''
            ]
        ]
        
        header_table = Table(header_data, colWidths=[4*inch, 2*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        elements.append(header_table)
        return elements
    
    def _build_invoice_info(self, invoice):
        """Build invoice information and client details"""
        elements = []
        
        # Invoice details and client info side by side
        invoice_info = [
            f"<b>Invoice Number:</b> {invoice.invoice_number}",
            f"<b>Issue Date:</b> {invoice.issue_date.strftime('%B %d, %Y')}",
            f"<b>Due Date:</b> {invoice.due_date.strftime('%B %d, %Y')}",
            f"<b>Status:</b> {invoice.get_status_display()}"
        ]
        
        client_info = [
            f"<b>Bill To:</b>",
            f"{invoice.client.name}",
            f"{invoice.client.email}",
            f"{invoice.client.address}"
        ]
        
        if invoice.mandate:
            invoice_info.append(f"<b>Matter:</b> {invoice.mandate.name}")
        
        info_data = [
            [
                Paragraph('<br/>'.join(invoice_info), self.styles['Normal']),
                Paragraph('<br/>'.join(client_info), self.styles['Normal'])
            ]
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ]))
        
        elements.append(info_table)
        return elements
    
    def _build_line_items_table(self, invoice):
        """Build the line items table"""
        elements = []
        
        # Table headers
        headers = ['Description', 'Quantity', 'Rate', 'Amount']
        table_data = [headers]
        
        # Add line items
        for item in invoice.line_items.all():
            table_data.append([
                Paragraph(item.description, self.styles['Normal']),
                f"{item.quantity:,.2f}",
                f"${item.unit_rate:,.2f}",
                f"${item.total_amount:,.2f}"
            ])
        
        # Create table
        table = Table(table_data, colWidths=[3.5*inch, 1*inch, 1*inch, 1.5*inch])
        
        # Style the table
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Right align numbers
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Left align descriptions
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        elements.append(table)
        return elements
    
    def _build_totals_section(self, invoice):
        """Build the totals section"""
        elements = []
        
        # Create totals table (right-aligned)
        totals_data = [
            ['Subtotal:', f"${invoice.subtotal:,.2f}"],
            [f'Tax ({invoice.tax_rate}%):', f"${invoice.tax_amount:,.2f}"],
            ['Total Amount:', f"${invoice.total_amount:,.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[1.5*inch, 1.5*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        
        # Create container table to right-align the totals
        container_data = [['', totals_table]]
        container_table = Table(container_data, colWidths=[4*inch, 3*inch])
        container_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(container_table)
        return elements
    
    def _build_notes_section(self, invoice):
        """Build the notes section"""
        elements = []
        
        elements.append(Paragraph('Notes:', self.styles['SectionHeader']))
        elements.append(Paragraph(invoice.notes, self.styles['Normal']))
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _build_payment_terms(self):
        """Build payment terms section"""
        elements = []
        
        payment_terms = [
            "Payment Terms:",
            "• Payment is due within 30 days of invoice date",
            "• Late payments may incur additional charges",
            "• Please include invoice number with payment",
            f"• For questions, contact: {self.company_info['email']}"
        ]
        
        elements.append(Paragraph('Payment Information:', self.styles['SectionHeader']))
        elements.append(Paragraph('<br/>'.join(payment_terms), self.styles['Normal']))
        
        return elements
    
    def generate_invoice_filename(self, invoice):
        """Generate a standardized filename for the invoice PDF"""
        client_name = invoice.client.name.replace(' ', '_').replace('/', '_')
        return f"Invoice_{invoice.invoice_number}_{client_name}.pdf"


class InvoiceSummaryPDFGenerator:
    """Generate summary reports for multiple invoices"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_invoice_summary_pdf(self, invoices, title="Invoice Summary Report"):
        """
        Generate a summary PDF for multiple invoices
        
        Args:
            invoices: QuerySet or list of Invoice instances
            title: Report title
            
        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        story = []
        
        # Title
        story.append(Paragraph(title, self.styles['Title']))
        story.append(Paragraph(f"Generated on {date.today().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 24))
        
        # Summary statistics
        total_amount = sum(invoice.total_amount for invoice in invoices)
        paid_amount = sum(invoice.total_amount for invoice in invoices if invoice.status == 'paid')
        outstanding_amount = total_amount - paid_amount
        
        stats_data = [
            ['Total Invoices:', str(len(invoices))],
            ['Total Amount:', f"${total_amount:,.2f}"],
            ['Paid Amount:', f"${paid_amount:,.2f}"],
            ['Outstanding:', f"${outstanding_amount:,.2f}"]
        ]
        
        stats_table = Table(stats_data)
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 24))
        
        # Invoice list table
        headers = ['Invoice #', 'Client', 'Date', 'Due Date', 'Amount', 'Status']
        table_data = [headers]
        
        for invoice in invoices:
            table_data.append([
                invoice.invoice_number,
                invoice.client.name,
                invoice.issue_date.strftime('%m/%d/%Y'),
                invoice.due_date.strftime('%m/%d/%Y'),
                f"${invoice.total_amount:,.2f}",
                invoice.get_status_display()
            ])
        
        invoice_table = Table(table_data)
        invoice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(invoice_table)
        
        doc.build(story)
        buffer.seek(0)
        return buffer