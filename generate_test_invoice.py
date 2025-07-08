#!/usr/bin/env python
"""
Script to generate test invoices and PDFs for testing purposes.

Usage:
    python generate_test_invoice.py
    
This script will:
1. Create a test invoice from unbilled time entries
2. Generate and save a PDF file
3. Optionally test email functionality

Prerequisites:
- Django environment must be set up
- Database with test data (clients, lawyers, mandates, time entries)
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_backend.settings')
django.setup()

from core.models import Client, Lawyer, Mandate, TimeEntry, Invoice
from core.services import InvoiceGeneratorService
from core.pdf_generator import InvoicePDFGenerator
from core.email_service import InvoiceEmailService
from django.conf import settings


def create_test_invoice(client_id=None, mandate_id=None):
    """
    Create a test invoice from unbilled time entries
    
    Args:
        client_id: Optional client ID, defaults to first client with unbilled entries
        mandate_id: Optional mandate ID, filters entries by mandate
    
    Returns:
        Invoice instance
    """
    print("=== CREATING TEST INVOICE ===")
    
    # Get client
    if client_id:
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            print(f"Client with ID {client_id} not found")
            return None
    else:
        # Find first client with unbilled entries
        clients_with_entries = Client.objects.filter(
            mandates__time_entries__is_billable=True,
            mandates__time_entries__is_invoiced=False
        ).distinct()
        
        if clients_with_entries.exists():
            client = clients_with_entries.first()
        else:
            client = Client.objects.first()
            if not client:
                print("No clients found in database")
                return None
    
    print(f"Client: {client.name} ({client.email})")
    
    # Get mandate if specified
    mandate = None
    if mandate_id:
        try:
            mandate = Mandate.objects.get(id=mandate_id, client=client)
            print(f"Mandate: {mandate.name}")
        except Mandate.DoesNotExist:
            print(f"Mandate with ID {mandate_id} not found for client {client.name}")
            return None
    
    # Get unbilled time entries
    unbilled_entries = TimeEntry.objects.filter(
        mandate__client=client,
        is_billable=True,
        is_invoiced=False
    )
    
    if mandate:
        unbilled_entries = unbilled_entries.filter(mandate=mandate)
    
    if not unbilled_entries.exists():
        print(f"No unbilled time entries found for client {client.name}")
        return None
    
    print(f"Found {unbilled_entries.count()} unbilled time entries")
    for entry in unbilled_entries:
        print(f"  - {entry.date}: {entry.hours}h @ ${entry.lawyer.hourly_rate}/h = ${entry.cost}")
    
    # Create invoice
    generator = InvoiceGeneratorService()
    invoice = generator.generate_invoice_from_time_entries(
        client=client,
        time_entries=unbilled_entries,
        due_days=30,
        mandate=mandate
    )
    
    print(f"\n✅ Invoice created successfully!")
    print(f"Invoice Number: {invoice.invoice_number}")
    print(f"Total Amount: ${invoice.total_amount}")
    print(f"Status: {invoice.status}")
    print(f"Due Date: {invoice.due_date}")
    
    return invoice


def generate_pdf(invoice, save_path=None):
    """
    Generate PDF for an invoice
    
    Args:
        invoice: Invoice instance
        save_path: Optional path to save PDF, defaults to current directory
    
    Returns:
        str: Path to saved PDF file
    """
    print("\n=== GENERATING PDF ===")
    
    pdf_generator = InvoicePDFGenerator()
    pdf_buffer = pdf_generator.generate_invoice_pdf(invoice)
    
    if save_path is None:
        filename = pdf_generator.generate_invoice_filename(invoice)
    else:
        filename = save_path
    
    # Save PDF to file
    with open(filename, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    file_size = os.path.getsize(filename)
    full_path = os.path.abspath(filename)
    
    print(f"✅ PDF generated successfully!")
    print(f"Filename: {filename}")
    print(f"Full path: {full_path}")
    print(f"File size: {file_size:,} bytes")
    
    return full_path


def test_email(invoice, send_pdf=True, test_mode=True):
    """
    Test email functionality
    
    Args:
        invoice: Invoice instance
        send_pdf: Whether to attach PDF
        test_mode: If True, uses console backend for testing
    
    Returns:
        bool: Success status
    """
    print("\n=== TESTING EMAIL ===")
    
    if test_mode:
        # Use console backend for testing
        settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
        print("Using console email backend for testing")
    
    email_service = InvoiceEmailService()
    
    try:
        result = email_service.send_invoice_email(
            invoice=invoice,
            custom_message="This is a test invoice generated by the test script.",
            send_pdf=send_pdf
        )
        
        if result:
            print("✅ Email sent successfully!")
            print(f"Invoice status updated to: {invoice.status}")
        else:
            print("❌ Email sending failed")
        
        return result
        
    except Exception as e:
        print(f"❌ Email error: {str(e)}")
        return False


def show_invoice_details(invoice):
    """Display detailed invoice information"""
    print(f"\n=== INVOICE DETAILS ===")
    print(f"Invoice Number: {invoice.invoice_number}")
    print(f"Client: {invoice.client.name}")
    print(f"Email: {invoice.client.email}")
    print(f"Issue Date: {invoice.issue_date}")
    print(f"Due Date: {invoice.due_date}")
    print(f"Status: {invoice.get_status_display()}")
    if invoice.mandate:
        print(f"Mandate: {invoice.mandate.name}")
    
    print(f"\nLine Items:")
    for item in invoice.line_items.all():
        print(f"  - {item.description[:50]}...")
        print(f"    Quantity: {item.quantity}, Rate: ${item.unit_rate}, Total: ${item.total_amount}")
    
    print(f"\nTotals:")
    print(f"  Subtotal: ${invoice.subtotal}")
    print(f"  Tax ({invoice.tax_rate}%): ${invoice.tax_amount}")
    print(f"  Total: ${invoice.total_amount}")


def main():
    """Main function to run the test invoice generation"""
    print("🚀 Test Invoice Generator")
    print("=" * 50)
    
    # Check if we have data
    client_count = Client.objects.count()
    entry_count = TimeEntry.objects.filter(is_billable=True, is_invoiced=False).count()
    
    print(f"Database status:")
    print(f"  Clients: {client_count}")
    print(f"  Unbilled time entries: {entry_count}")
    
    if client_count == 0:
        print("❌ No clients found. Please add test data first.")
        return
    
    if entry_count == 0:
        print("❌ No unbilled time entries found. Please add test data first.")
        return
    
    # Create test invoice
    invoice = create_test_invoice()
    if not invoice:
        print("❌ Failed to create invoice")
        return
    
    # Show details
    show_invoice_details(invoice)
    
    # Generate PDF
    pdf_path = generate_pdf(invoice)
    
    # Test email (optional)
    try:
        print(f"\nWould you like to test email functionality? (y/n): ", end="")
        response = input().lower().strip()
        if response in ['y', 'yes']:
            test_email(invoice, send_pdf=True, test_mode=True)
    except (EOFError, KeyboardInterrupt):
        print("Skipping email test...")
    
    print(f"\n🎉 Test completed successfully!")
    print(f"📄 PDF saved at: {pdf_path}")
    print(f"💰 Invoice: {invoice.invoice_number} (${invoice.total_amount})")


if __name__ == "__main__":
    main()