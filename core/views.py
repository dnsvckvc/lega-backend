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
    """
    Client Management API
    
    Provides CRUD operations for legal clients. Clients are the entities that engage
    the law firm for legal services.
    
    **Permissions:**
    - **Read access:** All authenticated users
    - **Write access:** Admin lawyers only
    
    **Filtering & Search:**
    - Search by: name, email
    - Order by: name, created_at
    - Default ordering: alphabetical by name
    
    **Available Actions:**
    - `GET /api/clients/` - List all clients
    - `POST /api/clients/` - Create new client (admin only)
    - `GET /api/clients/{id}/` - Retrieve client details
    - `PUT/PATCH /api/clients/{id}/` - Update client (admin only)
    - `DELETE /api/clients/{id}/` - Delete client (admin only)
    - `GET /api/clients/{id}/mandates/` - Get client's mandates
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def mandates(self, request, pk=None):
        """
        Get Client's Mandates
        
        Retrieve all mandates (legal projects) associated with this client.
        Results are filtered based on user permissions.
        
        **Returns:** List of mandates for the specified client
        """
        client = self.get_object()
        mandates = client.mandates.all()
        serializer = MandateSerializer(mandates, many=True)
        return Response(serializer.data)


class LawyerViewSet(viewsets.ModelViewSet):
    """
    Lawyer Management API
    
    Manages lawyer profiles and billing information. Lawyers are staff members
    who provide legal services and track billable time.
    
    **Permissions:**
    - **Read access:** All authenticated users
    - **Write access:** Admin lawyers only
    
    **Filtering & Search:**
    - Search by: name, email
    - Order by: name, hourly_rate, created_at
    - Default ordering: alphabetical by name
    
    **Available Actions:**
    - `GET /api/lawyers/` - List all lawyers
    - `POST /api/lawyers/` - Create new lawyer (admin only)
    - `GET /api/lawyers/{id}/` - Retrieve lawyer details
    - `PUT/PATCH /api/lawyers/{id}/` - Update lawyer (admin only)
    - `DELETE /api/lawyers/{id}/` - Delete lawyer (admin only)
    - `GET /api/lawyers/{id}/mandates/` - Get lawyer's mandates
    - `GET /api/lawyers/{id}/time_entries/` - Get lawyer's time entries
    - `GET /api/lawyers/{id}/monthly_billing/` - Get monthly billing summary
    """
    queryset = Lawyer.objects.all()
    serializer_class = LawyerSerializer
    permission_classes = [ReadOnlyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email']
    ordering_fields = ['name', 'hourly_rate', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def mandates(self, request, pk=None):
        """
        Get Lawyer's Mandates
        
        Retrieve all mandates assigned to this lawyer.
        Results are filtered based on user permissions.
        
        **Returns:** List of mandates assigned to the specified lawyer
        """
        lawyer = self.get_object()
        mandates = lawyer.mandates.all()
        serializer = MandateSerializer(mandates, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def time_entries(self, request, pk=None):
        """
        Get Lawyer's Time Entries
        
        Retrieve all time entries recorded by this lawyer.
        Results are filtered based on user permissions.
        
        **Returns:** List of time entries by the specified lawyer
        """
        lawyer = self.get_object()
        time_entries = lawyer.time_entries.all()
        serializer = TimeEntrySerializer(time_entries, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def monthly_billing(self, request, pk=None):
        """
        Get Lawyer's Monthly Billing Summary
        
        Calculate billing summary for a lawyer for a specific month.
        Includes total hours, amount, and breakdown by mandate.
        
        **Query Parameters:**
        - `month` (optional): Month number (1-12), defaults to current month
        - `year` (optional): Year (YYYY), defaults to current year
        
        **Returns:**
        - Lawyer information
        - Total hours and billing amount
        - Breakdown by mandate/client
        - Individual time entries details
        
        **Example:** `/api/lawyers/1/monthly_billing/?month=6&year=2025`
        """
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
    """
    Mandate (Legal Project) Management API
    
    Manages legal mandates/projects. Mandates represent specific legal matters
    handled for clients, with assigned lawyers and tracked time.
    
    **Permissions:**
    - **Admin lawyers:** Full access to all mandates
    - **Regular lawyers:** Access only to assigned mandates, limited write permissions
    
    **Filtering & Search:**
    - Filter by: client, lawyers, due_date
    - Search by: name, description, client name
    - Order by: name, due_date, created_at
    - Special status filters: active, inactive, overdue
    
    **Available Actions:**
    - `GET /api/mandates/` - List mandates (role-filtered)
    - `POST /api/mandates/` - Create new mandate
    - `GET /api/mandates/{id}/` - Retrieve mandate details
    - `PUT/PATCH /api/mandates/{id}/` - Update mandate (permissions apply)
    - `DELETE /api/mandates/{id}/` - Delete mandate (admin only)
    - `GET /api/mandates/{id}/summary/` - Get mandate summary with costs
    - `GET /api/mandates/{id}/time_entries/` - Get mandate's time entries
    """
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
    """
    Time Entry Management API
    
    Manages billable time entries for legal work. Time entries record the hours
    spent by lawyers on specific mandates, forming the basis for client billing.
    
    **Permissions:**
    - **Admin lawyers:** Full access to all time entries
    - **Regular lawyers:** Access only to their own time entries
    
    **Filtering & Search:**
    - Filter by: mandate, lawyer, date, date_from, date_to
    - Search by: description, mandate name, lawyer name
    - Order by: date, hours, created_at
    - Default ordering: newest entries first
    
    **Available Actions:**
    - `GET /api/time-entries/` - List time entries (role-filtered)
    - `POST /api/time-entries/` - Create new time entry
    - `GET /api/time-entries/{id}/` - Retrieve time entry details
    - `PUT/PATCH /api/time-entries/{id}/` - Update time entry (own entries only for regular lawyers)
    - `DELETE /api/time-entries/{id}/` - Delete time entry (own entries only for regular lawyers)
    
    **Date Range Filtering:**
    Use `date_from` and `date_to` parameters for filtering by date ranges.
    Example: `/api/time-entries/?date_from=2025-07-01&date_to=2025-07-31`
    
    **Automatic Lawyer Assignment:**
    Regular lawyers automatically have their lawyer profile assigned to new time entries.
    Admin lawyers can specify any lawyer when creating time entries.
    """
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
