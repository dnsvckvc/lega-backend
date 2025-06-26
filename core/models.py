from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def cost(self):
        return self.hours * self.lawyer.hourly_rate

    def __str__(self):
        return f"{self.lawyer.name} - {self.mandate.name} - {self.hours}h on {self.date}"

    class Meta:
        ordering = ['-date', '-created_at']
