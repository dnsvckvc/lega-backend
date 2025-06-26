from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'lawyer_profile', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Legal Practice Info', {
            'fields': ('role', 'lawyer_profile'),
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Legal Practice Info', {
            'fields': ('email', 'first_name', 'last_name', 'role'),
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('lawyer_profile')