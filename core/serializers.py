from rest_framework import serializers
from .models import Client, Lawyer, Mandate, TimeEntry, Invoice, InvoiceLineItem, ChangeLog
from datetime import date, datetime
from decimal import Decimal
import json


class ClientSerializer(serializers.ModelSerializer):
    mandates_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'address', 'created_at', 'updated_at', 'mandates_count']
        read_only_fields = ['created_at', 'updated_at']

    def get_mandates_count(self, obj):
        return obj.mandates.count()


class LawyerSerializer(serializers.ModelSerializer):
    mandates_count = serializers.SerializerMethodField()

    class Meta:
        model = Lawyer
        fields = ['id', 'name', 'email', 'phone', 'hourly_rate', 'created_at', 'updated_at', 'mandates_count']
        read_only_fields = ['created_at', 'updated_at']

    def get_mandates_count(self, obj):
        return obj.mandates.count()


class MandateSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    lawyers_names = serializers.SerializerMethodField()
    total_hours = serializers.ReadOnlyField()
    total_cost = serializers.ReadOnlyField()
    time_entries_count = serializers.SerializerMethodField()

    class Meta:
        model = Mandate
        fields = [
            'id', 'name', 'description', 'client', 'client_name', 
            'lawyers', 'lawyers_names', 'due_date', 'cost_ceiling', 'is_active',
            'total_hours', 'total_cost', 'time_entries_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_lawyers_names(self, obj):
        return [lawyer.name for lawyer in obj.lawyers.all()]

    def get_time_entries_count(self, obj):
        return obj.time_entries.count()


class TimeEntrySerializer(serializers.ModelSerializer):
    mandate_name = serializers.CharField(source='mandate.name', read_only=True)
    lawyer_name = serializers.CharField(source='lawyer.name', read_only=True)
    cost = serializers.ReadOnlyField()

    class Meta:
        model = TimeEntry
        fields = [
            'id', 'mandate', 'mandate_name', 'lawyer', 'lawyer_name',
            'date', 'hours', 'description', 'is_billable', 'is_invoiced', 
            'cost', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        mandate = data.get('mandate')
        lawyer = data.get('lawyer')
        
        if mandate and lawyer and lawyer not in mandate.lawyers.all():
            raise serializers.ValidationError(
                "The selected lawyer is not assigned to this mandate."
            )
        
        return data


class MandateDetailSerializer(MandateSerializer):
    time_entries = TimeEntrySerializer(many=True, read_only=True)

    class Meta(MandateSerializer.Meta):
        fields = MandateSerializer.Meta.fields + ['time_entries']


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    time_entry_description = serializers.CharField(source='time_entry.description', read_only=True)
    
    class Meta:
        model = InvoiceLineItem
        fields = [
            'id', 'description', 'quantity', 'unit_rate', 'total_amount',
            'time_entry', 'time_entry_description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount', 'created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_email = serializers.CharField(source='client.email', read_only=True)
    mandate_name = serializers.CharField(source='mandate.name', read_only=True)
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client', 'client_name', 'client_email',
            'mandate', 'mandate_name', 'issue_date', 'due_date', 'status',
            'subtotal', 'tax_rate', 'tax_amount', 'total_amount',
            'notes', 'paid_date', 'is_overdue', 'line_items',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'invoice_number', 'subtotal', 'tax_amount', 'total_amount',
            'is_overdue', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        # Ensure due date is after issue date
        issue_date = data.get('issue_date')
        due_date = data.get('due_date')
        
        if issue_date and due_date and due_date <= issue_date:
            raise serializers.ValidationError("Due date must be after issue date.")
        
        return data


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invoices with line items"""
    line_items = InvoiceLineItemSerializer(many=True, write_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'client', 'mandate', 'due_date', 'tax_rate', 'notes', 'line_items'
        ]
    
    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        invoice = Invoice.objects.create(**validated_data)
        
        for item_data in line_items_data:
            InvoiceLineItem.objects.create(invoice=invoice, **item_data)
        
        # Calculate totals
        invoice.calculate_totals()
        invoice.save()
        
        return invoice


class InvoiceStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating invoice status"""
    status = serializers.ChoiceField(choices=Invoice.STATUS_CHOICES)
    paid_date = serializers.DateField(required=False, allow_null=True)
    
    def validate(self, data):
        status = data.get('status')
        paid_date = data.get('paid_date')
        
        if status == 'paid' and not paid_date:
            from datetime import date
            data['paid_date'] = date.today()
        elif status != 'paid':
            data['paid_date'] = None
            
        return data


class InvoiceGenerationSerializer(serializers.Serializer):
    """Serializer for generating invoices from time entries"""
    client_id = serializers.IntegerField()
    mandate_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    due_days = serializers.IntegerField(default=30, min_value=1)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=21.00)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date.")
        
        # Validate client exists
        try:
            Client.objects.get(id=data['client_id'])
        except Client.DoesNotExist:
            raise serializers.ValidationError("Client not found.")
        
        # Validate mandate if provided
        mandate_id = data.get('mandate_id')
        if mandate_id:
            try:
                mandate = Mandate.objects.get(id=mandate_id)
                if mandate.client_id != data['client_id']:
                    raise serializers.ValidationError("Mandate does not belong to the specified client.")
            except Mandate.DoesNotExist:
                raise serializers.ValidationError("Mandate not found.")
        
        return data


class InvoiceSummarySerializer(serializers.Serializer):
    """Serializer for invoice summary reports"""
    total_invoices = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_count = serializers.IntegerField()
    overdue_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class ChangeLogSerializer(serializers.ModelSerializer):
    """
    Serializer for change log entries.
    """
    model_name = serializers.ReadOnlyField()
    app_label = serializers.ReadOnlyField()
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    old_value_parsed = serializers.SerializerMethodField()
    new_value_parsed = serializers.SerializerMethodField()
    
    class Meta:
        model = ChangeLog
        fields = [
            'id', 'model_name', 'app_label', 'object_id', 'field_name',
            'old_value', 'new_value', 'old_value_parsed', 'new_value_parsed',
            'change_type', 'changed_by', 'changed_by_email', 'changed_by_name',
            'changed_at', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'changed_at']
    
    def get_old_value_parsed(self, obj):
        """Parse old_value from JSON string to appropriate type."""
        if obj.old_value is None:
            return None
        try:
            return json.loads(obj.old_value)
        except (json.JSONDecodeError, TypeError):
            return obj.old_value
    
    def get_new_value_parsed(self, obj):
        """Parse new_value from JSON string to appropriate type."""
        if obj.new_value is None:
            return None
        try:
            return json.loads(obj.new_value)
        except (json.JSONDecodeError, TypeError):
            return obj.new_value


class ChangeLogListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for change log list views.
    """
    model_name = serializers.ReadOnlyField()
    changed_by_email = serializers.CharField(source='changed_by.email', read_only=True)
    old_value_parsed = serializers.SerializerMethodField()
    new_value_parsed = serializers.SerializerMethodField()
    
    class Meta:
        model = ChangeLog
        fields = [
            'id', 'model_name', 'object_id', 'field_name',
            'old_value_parsed', 'new_value_parsed', 'change_type',
            'changed_by_email', 'changed_at'
        ]
    
    def get_old_value_parsed(self, obj):
        """Parse old_value from JSON string to appropriate type."""
        if obj.old_value is None:
            return None
        try:
            return json.loads(obj.old_value)
        except (json.JSONDecodeError, TypeError):
            return obj.old_value
    
    def get_new_value_parsed(self, obj):
        """Parse new_value from JSON string to appropriate type."""
        if obj.new_value is None:
            return None
        try:
            return json.loads(obj.new_value)
        except (json.JSONDecodeError, TypeError):
            return obj.new_value