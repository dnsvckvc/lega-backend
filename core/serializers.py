from rest_framework import serializers
from .models import Client, Lawyer, Mandate, TimeEntry


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
            'date', 'hours', 'description', 'cost', 'created_at', 'updated_at'
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