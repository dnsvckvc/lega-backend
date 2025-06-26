from django.contrib import admin
from .models import Client, Lawyer, Mandate, TimeEntry


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'hourly_rate', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Mandate)
class MandateAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'is_active', 'due_date', 'cost_ceiling', 'created_at']
    list_filter = ['is_active', 'due_date', 'created_at', 'client']
    search_fields = ['name', 'description', 'client__name']
    filter_horizontal = ['lawyers']
    readonly_fields = ['created_at', 'updated_at', 'total_hours', 'total_cost']
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'client', 'lawyers', 'is_active')
        }),
        ('Dates and Costs', {
            'fields': ('due_date', 'cost_ceiling')
        }),
        ('Summary', {
            'fields': ('total_hours', 'total_cost'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['mandate', 'lawyer', 'date', 'hours', 'cost', 'created_at']
    list_filter = ['date', 'created_at', 'mandate', 'lawyer']
    search_fields = ['mandate__name', 'lawyer__name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'cost']
    date_hierarchy = 'date'

    def cost(self, obj):
        return f"${obj.cost:.2f}"
    cost.short_description = 'Cost'
