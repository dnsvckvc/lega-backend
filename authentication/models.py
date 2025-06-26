from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for the legal practice management system.
    Extends Django's AbstractUser to include role-based permissions.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin Lawyer'),
        ('lawyer', 'Regular Lawyer'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='lawyer',
        help_text="User role determines access permissions"
    )
    lawyer_profile = models.OneToOneField(
        'core.Lawyer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account',
        help_text="Link to lawyer profile for data access permissions"
    )
    
    # Use email as the primary login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_admin_lawyer(self):
        """Check if user is an admin lawyer with full permissions"""
        return self.role == 'admin'
    
    @property
    def is_regular_lawyer(self):
        """Check if user is a regular lawyer with limited permissions"""
        return self.role == 'lawyer'
    
    def can_access_mandate(self, mandate):
        """
        Check if user can access a specific mandate.
        Admin lawyers can access all mandates.
        Regular lawyers can only access mandates they're assigned to.
        """
        if self.is_admin_lawyer:
            return True
        
        if self.lawyer_profile and mandate.lawyers.filter(id=self.lawyer_profile.id).exists():
            return True
            
        return False
    
    def can_access_time_entry(self, time_entry):
        """
        Check if user can access a specific time entry.
        Admin lawyers can access all time entries.
        Regular lawyers can only access their own time entries.
        """
        if self.is_admin_lawyer:
            return True
            
        if self.lawyer_profile and time_entry.lawyer == self.lawyer_profile:
            return True
            
        return False