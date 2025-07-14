from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
from decimal import Decimal
from datetime import date


class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Lawyer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Mandate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='mandates')
    lawyers = models.ManyToManyField(Lawyer, related_name='mandates')
    due_date = models.DateField()
    cost_ceiling = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this mandate is currently active. Can be set to False when mandate is completed or cancelled."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.client.name}"

    @property
    def total_hours(self):
        return sum(entry.hours for entry in self.time_entries.all())

    @property
    def total_cost(self):
        return sum(entry.cost for entry in self.time_entries.all())

    class Meta:
        ordering = ['-created_at']


class TimeEntry(models.Model):
    mandate = models.ForeignKey(Mandate, on_delete=models.CASCADE, related_name='time_entries')
    lawyer = models.ForeignKey(Lawyer, on_delete=models.CASCADE, related_name='time_entries')
    date = models.DateField()
    hours = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    description = models.TextField(blank=True)
    is_billable = models.BooleanField(default=True)
    is_invoiced = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def cost(self):
        return self.hours * self.lawyer.hourly_rate

    def __str__(self):
        return f"{self.lawyer.name} - {self.mandate.name} - {self.hours}h on {self.date}"

    class Meta:
        ordering = ['-date', '-created_at']


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    mandate = models.ForeignKey(Mandate, on_delete=models.CASCADE, related_name='invoices', null=True, blank=True)
    issue_date = models.DateField(default=date.today)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    subtotal = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('21.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    tax_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    notes = models.TextField(blank=True)
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.client.name}"
    
    def calculate_totals(self):
        self.subtotal = sum(item.total_amount for item in self.line_items.all())
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount
        
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
        
    def generate_invoice_number(self):
        current_year = date.today().year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f"INV-{current_year}"
        ).order_by('invoice_number').last()
        
        if last_invoice:
            last_number = int(last_invoice.invoice_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
            
        return f"INV-{current_year}-{new_number:04d}"
    
    @property
    def is_overdue(self):
        return self.status == 'sent' and self.due_date < date.today()
    
    class Meta:
        ordering = ['-created_at']


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    time_entry = models.ForeignKey(TimeEntry, on_delete=models.CASCADE, null=True, blank=True)
    
    description = models.TextField()
    quantity = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    unit_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_rate
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description[:50]}"
    
    class Meta:
        ordering = ['created_at']


class ChangeLog(models.Model):
    """
    Unified change tracking for Client, Mandate, and TimeEntry models.
    Tracks all field changes with old and new values.
    """
    CHANGE_TYPE_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    
    # Generic foreign key to track changes for any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Change details
    field_name = models.CharField(max_length=100, help_text="Name of the field that changed")
    old_value = models.TextField(null=True, blank=True, help_text="Previous value (JSON serialized)")
    new_value = models.TextField(null=True, blank=True, help_text="New value (JSON serialized)")
    change_type = models.CharField(
        max_length=20, 
        choices=CHANGE_TYPE_CHOICES,
        help_text="Type of change operation"
    )
    
    # Metadata
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text="User who made the change"
    )
    changed_at = models.DateTimeField(auto_now_add=True, help_text="When the change occurred")
    
    # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the user")
    user_agent = models.TextField(null=True, blank=True, help_text="User agent string")
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['changed_by']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['change_type']),
        ]
    
    def __str__(self):
        return f"{self.content_type.model} #{self.object_id} - {self.field_name} {self.change_type.lower()}d by {self.changed_by.email}"
    
    @property
    def model_name(self):
        """Return the model name for the tracked object."""
        return self.content_type.model
    
    @property
    def app_label(self):
        """Return the app label for the tracked object."""
        return self.content_type.app_label
