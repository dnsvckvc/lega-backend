#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/dvuckovac/projects/vibe/claude-first')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'legal_backend.settings')
django.setup()

try:
    from core.models import Invoice, InvoiceLineItem, TimeEntry
    print("✓ Models imported successfully")
    print(f"✓ Invoice model: {Invoice}")
    print(f"✓ InvoiceLineItem model: {InvoiceLineItem}")
    print(f"✓ TimeEntry model updated: {TimeEntry}")
    
    # Test model field access
    print("✓ Testing model fields:")
    invoice_fields = [f.name for f in Invoice._meta.fields]
    print(f"  Invoice fields: {invoice_fields}")
    
    line_item_fields = [f.name for f in InvoiceLineItem._meta.fields]
    print(f"  InvoiceLineItem fields: {line_item_fields}")
    
    print("✓ All models are valid - ready for migrations")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Model validation error: {e}")