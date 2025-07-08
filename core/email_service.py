from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .pdf_generator import InvoicePDFGenerator
import logging

logger = logging.getLogger(__name__)


class InvoiceEmailService:
    """Service for sending invoice emails to clients"""
    
    def __init__(self):
        self.pdf_generator = InvoicePDFGenerator()
    
    def send_invoice_email(self, invoice, custom_message="", send_pdf=True):
        """
        Send an invoice email to the client
        
        Args:
            invoice: Invoice instance
            custom_message: Custom message to include in email
            send_pdf: Whether to attach PDF
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Prepare email context
            context = {
                'invoice': invoice,
                'client': invoice.client,
                'custom_message': custom_message,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Legal Practice Management'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'billing@legalpractice.com'),
                'company_phone': getattr(settings, 'COMPANY_PHONE', '+1 (555) 123-4567'),
            }
            
            # Render email templates
            html_content = render_to_string('emails/invoice_email.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Invoice {invoice.invoice_number} from {context['company_name']}"
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.client.email],
                reply_to=[context['company_email']]
            )
            email.content_subtype = 'html'
            
            # Attach PDF if requested
            if send_pdf:
                pdf_buffer = self.pdf_generator.generate_invoice_pdf(invoice)
                filename = self.pdf_generator.generate_invoice_filename(invoice)
                email.attach(filename, pdf_buffer.getvalue(), 'application/pdf')
            
            # Send email
            email.send()
            
            # Update invoice status to sent if it was draft
            if invoice.status == 'draft':
                invoice.status = 'sent'
                invoice.save()
            
            logger.info(f"Invoice email sent successfully for {invoice.invoice_number} to {invoice.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send invoice email for {invoice.invoice_number}: {str(e)}")
            return False
    
    def send_payment_reminder(self, invoice):
        """
        Send a payment reminder email for an overdue invoice
        
        Args:
            invoice: Invoice instance
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Calculate days overdue
            from datetime import date
            days_overdue = (date.today() - invoice.due_date).days
            
            context = {
                'invoice': invoice,
                'client': invoice.client,
                'days_overdue': days_overdue,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Legal Practice Management'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'billing@legalpractice.com'),
                'company_phone': getattr(settings, 'COMPANY_PHONE', '+1 (555) 123-4567'),
            }
            
            # Render email templates
            html_content = render_to_string('emails/payment_reminder.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Payment Reminder - Invoice {invoice.invoice_number} ({days_overdue} days overdue)"
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.client.email],
                reply_to=[context['company_email']]
            )
            email.content_subtype = 'html'
            
            # Attach PDF copy
            pdf_buffer = self.pdf_generator.generate_invoice_pdf(invoice)
            filename = self.pdf_generator.generate_invoice_filename(invoice)
            email.attach(filename, pdf_buffer.getvalue(), 'application/pdf')
            
            # Send email
            email.send()
            
            logger.info(f"Payment reminder sent for {invoice.invoice_number} to {invoice.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment reminder for {invoice.invoice_number}: {str(e)}")
            return False
    
    def send_payment_confirmation(self, invoice):
        """
        Send a payment confirmation email
        
        Args:
            invoice: Invoice instance (should be paid)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            context = {
                'invoice': invoice,
                'client': invoice.client,
                'company_name': getattr(settings, 'COMPANY_NAME', 'Legal Practice Management'),
                'company_email': getattr(settings, 'COMPANY_EMAIL', 'billing@legalpractice.com'),
            }
            
            # Render email templates
            html_content = render_to_string('emails/payment_confirmation.html', context)
            text_content = strip_tags(html_content)
            
            # Create email
            subject = f"Payment Received - Invoice {invoice.invoice_number}"
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invoice.client.email],
                reply_to=[context['company_email']]
            )
            email.content_subtype = 'html'
            
            # Send email
            email.send()
            
            logger.info(f"Payment confirmation sent for {invoice.invoice_number} to {invoice.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send payment confirmation for {invoice.invoice_number}: {str(e)}")
            return False
    
    def send_bulk_payment_reminders(self, overdue_invoices):
        """
        Send payment reminders for multiple overdue invoices
        
        Args:
            overdue_invoices: QuerySet or list of overdue Invoice instances
            
        Returns:
            dict: Summary of sent emails
        """
        results = {
            'sent_count': 0,
            'failed_count': 0,
            'failed_invoices': []
        }
        
        for invoice in overdue_invoices:
            if self.send_payment_reminder(invoice):
                results['sent_count'] += 1
            else:
                results['failed_count'] += 1
                results['failed_invoices'].append(invoice.invoice_number)
        
        logger.info(f"Bulk payment reminders: {results['sent_count']} sent, {results['failed_count']} failed")
        return results


class InvoiceNotificationService:
    """Service for automated invoice notifications and reminders"""
    
    def __init__(self):
        self.email_service = InvoiceEmailService()
    
    def send_overdue_reminders(self, days_overdue_threshold=7):
        """
        Send reminders for invoices that are overdue by specified days
        
        Args:
            days_overdue_threshold: Minimum days overdue to send reminder
            
        Returns:
            dict: Summary of notifications sent
        """
        from datetime import date, timedelta
        from .models import Invoice
        
        cutoff_date = date.today() - timedelta(days=days_overdue_threshold)
        
        overdue_invoices = Invoice.objects.filter(
            status='sent',
            due_date__lte=cutoff_date
        )
        
        return self.email_service.send_bulk_payment_reminders(overdue_invoices)
    
    def notify_upcoming_due_dates(self, days_ahead=3):
        """
        Send notifications for invoices due in specified days
        
        Args:
            days_ahead: Number of days ahead to check for due dates
            
        Returns:
            dict: Summary of notifications sent
        """
        from datetime import date, timedelta
        from .models import Invoice
        
        due_date = date.today() + timedelta(days=days_ahead)
        
        upcoming_invoices = Invoice.objects.filter(
            status='sent',
            due_date=due_date
        )
        
        results = {
            'sent_count': 0,
            'failed_count': 0,
            'failed_invoices': []
        }
        
        for invoice in upcoming_invoices:
            # Send gentle reminder about upcoming due date
            try:
                # This would require a new email template for due date reminders
                # For now, we'll use the payment reminder template
                if self.email_service.send_payment_reminder(invoice):
                    results['sent_count'] += 1
                else:
                    results['failed_count'] += 1
                    results['failed_invoices'].append(invoice.invoice_number)
            except Exception as e:
                logger.error(f"Failed to send due date reminder for {invoice.invoice_number}: {str(e)}")
                results['failed_count'] += 1
                results['failed_invoices'].append(invoice.invoice_number)
        
        return results