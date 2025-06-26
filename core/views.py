from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q
from datetime import date, datetime
from decimal import Decimal
from .models import Client, Lawyer, Mandate, TimeEntry
from .serializers import (
    ClientSerializer, LawyerSerializer, MandateSerializer, 
    MandateDetailSerializer, TimeEntrySerializer
)
from authentication.permissions import (
    IsAdminLawyer, ReadOnlyOrAdmin, CanAccessMandate, 
    CanAccessTimeEntry, CanModifyMandate
)


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def mandates(self, request, pk=None):
        client = self.get_object()
        mandates = client.mandates.all()
        serializer = MandateSerializer(mandates, many=True)
        return Response(serializer.data)


class LawyerViewSet(viewsets.ModelViewSet):
    queryset = Lawyer.objects.all()
    serializer_class = LawyerSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'hourly_rate', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def mandates(self, request, pk=None):
        lawyer = self.get_object()
        mandates = lawyer.mandates.all()
        serializer = MandateSerializer(mandates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def time_entries(self, request, pk=None):
        lawyer = self.get_object()
        time_entries = lawyer.time_entries.all()
        serializer = TimeEntrySerializer(time_entries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def monthly_billing(self, request, pk=None):
        lawyer = self.get_object()
        
        # Get month and year from query params, default to current month
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        try:
            if month and year:
                target_month = int(month)
                target_year = int(year)
            else:
                today = date.today()
                target_month = today.month
                target_year = today.year
        except (ValueError, TypeError):
            return Response({'error': 'Invalid month or year parameter'}, status=400)
        
        # Filter time entries for the specified month
        time_entries = lawyer.time_entries.filter(
            date__year=target_year,
            date__month=target_month
        )
        
        # Calculate totals
        total_hours = time_entries.aggregate(Sum('hours'))['hours__sum'] or Decimal('0')
        total_amount = sum(entry.cost for entry in time_entries)
        
        # Group by mandate
        mandate_breakdown = {}
        for entry in time_entries:
            mandate_name = entry.mandate.name
            if mandate_name not in mandate_breakdown:
                mandate_breakdown[mandate_name] = {
                    'mandate_id': entry.mandate.id,
                    'mandate_name': mandate_name,
                    'client_name': entry.mandate.client.name,
                    'hours': Decimal('0'),
                    'amount': Decimal('0'),
                    'entries': []
                }
            
            mandate_breakdown[mandate_name]['hours'] += entry.hours
            mandate_breakdown[mandate_name]['amount'] += entry.cost
            mandate_breakdown[mandate_name]['entries'].append({
                'date': entry.date,
                'hours': entry.hours,
                'cost': entry.cost,
                'description': entry.description
            })
        
        return Response({
            'lawyer_name': lawyer.name,
            'month': target_month,
            'year': target_year,
            'total_hours': total_hours,
            'total_amount': total_amount,
            'hourly_rate': lawyer.hourly_rate,
            'mandate_breakdown': list(mandate_breakdown.values()),
            'entries_count': time_entries.count()
        })


class MandateViewSet(viewsets.ModelViewSet):
    queryset = Mandate.objects.all()
    permission_classes = [CanModifyMandate]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'lawyers', 'due_date']
    search_fields = ['name', 'description', 'client__name']
    ordering_fields = ['name', 'due_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Mandate.objects.all()
        
        # Apply role-based filtering
        if not self.request.user.is_admin_lawyer:
            # Regular lawyers can only see mandates they're assigned to
            if self.request.user.lawyer_profile:
                queryset = queryset.filter(lawyers=self.request.user.lawyer_profile)
            else:
                # User has no lawyer profile, return empty queryset
                return Mandate.objects.none()
        
        # Custom filtering for active/inactive mandates based on is_active field
        status = self.request.query_params.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        elif status == 'overdue':
            # Overdue mandates: past due date AND still active
            queryset = queryset.filter(due_date__lt=date.today(), is_active=True)
        
        # Filter by is_active field directly
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                queryset = queryset.filter(is_active=False)
        
        # Filter by due date range
        due_date_from = self.request.query_params.get('due_date_from')
        due_date_to = self.request.query_params.get('due_date_to')
        
        if due_date_from:
            queryset = queryset.filter(due_date__gte=due_date_from)
        if due_date_to:
            queryset = queryset.filter(due_date__lte=due_date_to)
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MandateDetailSerializer
        return MandateSerializer

    @action(detail=True, methods=['get'])
    def time_entries(self, request, pk=None):
        mandate = self.get_object()
        time_entries = mandate.time_entries.all()
        serializer = TimeEntrySerializer(time_entries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        mandate = self.get_object()
        total_hours = mandate.time_entries.aggregate(Sum('hours'))['hours__sum'] or 0
        total_cost = sum(entry.cost for entry in mandate.time_entries.all())
        
        lawyer_breakdown = []
        for lawyer in mandate.lawyers.all():
            lawyer_entries = mandate.time_entries.filter(lawyer=lawyer)
            lawyer_hours = lawyer_entries.aggregate(Sum('hours'))['hours__sum'] or 0
            lawyer_cost = sum(entry.cost for entry in lawyer_entries)
            lawyer_breakdown.append({
                'lawyer_name': lawyer.name,
                'hours': lawyer_hours,
                'cost': lawyer_cost
            })

        return Response({
            'mandate_name': mandate.name,
            'client_name': mandate.client.name,
            'total_hours': total_hours,
            'total_cost': total_cost,
            'cost_ceiling': mandate.cost_ceiling,
            'cost_ceiling_exceeded': mandate.cost_ceiling and total_cost > mandate.cost_ceiling,
            'lawyer_breakdown': lawyer_breakdown
        })


class TimeEntryViewSet(viewsets.ModelViewSet):
    queryset = TimeEntry.objects.all()
    serializer_class = TimeEntrySerializer
    permission_classes = [CanAccessTimeEntry]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['mandate', 'lawyer', 'date']
    search_fields = ['description', 'mandate__name', 'lawyer__name']
    ordering_fields = ['date', 'hours', 'created_at']
    ordering = ['-date', '-created_at']

    def get_queryset(self):
        queryset = TimeEntry.objects.all()
        
        # Apply role-based filtering
        if not self.request.user.is_admin_lawyer:
            # Regular lawyers can only see their own time entries
            if self.request.user.lawyer_profile:
                queryset = queryset.filter(lawyer=self.request.user.lawyer_profile)
            else:
                # User has no lawyer profile, return empty queryset
                return TimeEntry.objects.none()
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
            
        return queryset
    
    def perform_create(self, serializer):
        # For regular lawyers, automatically set the lawyer to themselves
        if not self.request.user.is_admin_lawyer:
            if self.request.user.lawyer_profile:
                serializer.save(lawyer=self.request.user.lawyer_profile)
            else:
                raise permissions.PermissionDenied("You must have a lawyer profile to create time entries")
        else:
            serializer.save()
