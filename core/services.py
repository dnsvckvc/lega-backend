from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction
from django.db.models import Q
from .models import Invoice, InvoiceLineItem, TimeEntry, Client, Mandate


class InvoiceGeneratorService:
    """Service for generating invoices from time entries and other billable items"""
    
    def __init__(self, tax_rate=Decimal('21.00')):
        self.tax_rate = tax_rate
    
    def generate_invoice_from_time_entries(self, client, time_entries, due_days=30, mandate=None):
        """
        Generate an invoice from a list of time entries
        
        Args:
            client: Client instance
            time_entries: QuerySet or list of TimeEntry instances
            due_days: Number of days until invoice is due
            mandate: Optional Mandate instance to associate with invoice
        
        Returns:
            Invoice instance
        """
        if not time_entries:
            raise ValueError("No time entries provided for invoice generation")
        
        with transaction.atomic():
            # Create the invoice
            invoice = Invoice.objects.create(
                client=client,
                mandate=mandate,
                due_date=date.today() + timedelta(days=due_days),
                tax_rate=self.tax_rate
            )
            
            # Group time entries by lawyer and description for consolidation
            grouped_entries = self._group_time_entries(time_entries)
            
            # Create line items from grouped entries
            for group in grouped_entries:
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    description=group['description'],
                    quantity=group['total_hours'],
                    unit_rate=group['hourly_rate'],
                    total_amount=group['total_amount']
                )
            
            # Mark time entries as invoiced
            for entry in time_entries:
                entry.is_invoiced = True
                entry.save()
            
            # Calculate totals
            invoice.calculate_totals()
            invoice.save()
            
            return invoice
    
    def _group_time_entries(self, time_entries):
        """Group time entries by lawyer and create consolidated line items"""
        groups = {}
        
        for entry in time_entries:
            # Create a key for grouping (lawyer + rate)
            key = f"{entry.lawyer.name}_{entry.lawyer.hourly_rate}"
            
            if key not in groups:
                groups[key] = {
                    'description': f"Legal services - {entry.lawyer.name}",
                    'total_hours': Decimal('0.00'),
                    'hourly_rate': entry.lawyer.hourly_rate,
                    'total_amount': Decimal('0.00'),
                    'entries': []
                }
            
            groups[key]['total_hours'] += entry.hours
            groups[key]['total_amount'] += entry.cost
            groups[key]['entries'].append(entry)
        
        # Convert to list and add detailed descriptions
        result = []
        for group_data in groups.values():
            # Create detailed description from individual entries
            entry_details = []
            for entry in group_data['entries']:
                entry_details.append(f"{entry.date}: {entry.hours}h - {entry.description}")
            
            detailed_description = f"{group_data['description']}\n" + "\n".join(entry_details)
            
            result.append({
                'description': detailed_description,
                'total_hours': group_data['total_hours'],
                'hourly_rate': group_data['hourly_rate'],
                'total_amount': group_data['total_amount']
            })
        
        return result
    
    def generate_invoice_for_client_period(self, client, start_date, end_date, mandate=None):
        """
        Generate invoice for all unbilled time entries for a client in a date range
        
        Args:
            client: Client instance
            start_date: Start date for time entries
            end_date: End date for time entries
            mandate: Optional Mandate to filter by
        
        Returns:
            Invoice instance or None if no billable entries found
        """
        # Get unbilled time entries for the period
        time_entries = TimeEntry.objects.filter(
            mandate__client=client,
            date__gte=start_date,
            date__lte=end_date,
            is_billable=True,
            is_invoiced=False
        )
        
        if mandate:
            time_entries = time_entries.filter(mandate=mandate)
        
        if not time_entries.exists():
            return None
        
        return self.generate_invoice_from_time_entries(
            client=client,
            time_entries=time_entries,
            mandate=mandate
        )
    
    def generate_monthly_invoices_for_client(self, client, year, month):
        """
        Generate monthly invoice for a client
        
        Args:
            client: Client instance
            year: Year (int)
            month: Month (int)
        
        Returns:
            List of Invoice instances (one per mandate or one consolidated)
        """
        from calendar import monthrange
        
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])
        
        # Get all mandates with unbilled entries for this client
        mandates_with_entries = Mandate.objects.filter(
            client=client,
            time_entries__date__gte=start_date,
            time_entries__date__lte=end_date,
            time_entries__is_billable=True,
            time_entries__is_invoiced=False
        ).distinct()
        
        invoices = []
        for mandate in mandates_with_entries:
            invoice = self.generate_invoice_for_client_period(
                client=client,
                start_date=start_date,
                end_date=end_date,
                mandate=mandate
            )
            if invoice:
                invoices.append(invoice)
        
        return invoices
    
    def create_manual_invoice(self, client, line_items, mandate=None, due_days=30, notes=""):
        """
        Create a manual invoice with custom line items
        
        Args:
            client: Client instance
            line_items: List of dicts with 'description', 'quantity', 'unit_rate'
            mandate: Optional Mandate instance
            due_days: Days until due
            notes: Invoice notes
        
        Returns:
            Invoice instance
        """
        with transaction.atomic():
            invoice = Invoice.objects.create(
                client=client,
                mandate=mandate,
                due_date=date.today() + timedelta(days=due_days),
                tax_rate=self.tax_rate,
                notes=notes
            )
            
            for item in line_items:
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    description=item['description'],
                    quantity=item['quantity'],
                    unit_rate=item['unit_rate']
                )
            
            invoice.calculate_totals()
            invoice.save()
            
            return invoice


class InvoiceStatusService:
    """Service for managing invoice status and workflows"""
    
    @staticmethod
    def mark_as_sent(invoice):
        """Mark invoice as sent"""
        invoice.status = 'sent'
        invoice.save()
        return invoice
    
    @staticmethod
    def mark_as_paid(invoice, paid_date=None):
        """Mark invoice as paid"""
        invoice.status = 'paid'
        invoice.paid_date = paid_date or date.today()
        invoice.save()
        return invoice
    
    @staticmethod
    def mark_as_overdue(invoice):
        """Mark invoice as overdue"""
        invoice.status = 'overdue'
        invoice.save()
        return invoice
    
    @staticmethod
    def cancel_invoice(invoice):
        """Cancel an invoice"""
        if invoice.status == 'paid':
            raise ValueError("Cannot cancel a paid invoice")
        
        invoice.status = 'cancelled'
        invoice.save()
        
        # Unmark associated time entries as invoiced
        time_entry_ids = invoice.line_items.filter(
            time_entry__isnull=False
        ).values_list('time_entry_id', flat=True)
        
        TimeEntry.objects.filter(id__in=time_entry_ids).update(is_invoiced=False)
        
        return invoice
    
    @staticmethod
    def get_overdue_invoices():
        """Get all overdue invoices"""
        return Invoice.objects.filter(
            status='sent',
            due_date__lt=date.today()
        )
    
    @staticmethod
    def update_overdue_statuses():
        """Update all sent invoices that are past due to overdue status"""
        overdue_count = Invoice.objects.filter(
            status='sent',
            due_date__lt=date.today()
        ).update(status='overdue')
        
        return overdue_count