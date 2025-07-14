"""
Views for change log API endpoints.
"""

from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from .models import ChangeLog, Client, Mandate, TimeEntry
from .serializers import ChangeLogSerializer, ChangeLogListSerializer
from authentication.permissions import IsAdminLawyer


class ChangeLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Change Log API
    
    Provides read-only access to change log entries for Client, Mandate, and TimeEntry models.
    Tracks all field changes with old and new values, timestamps, and user information.
    
    **Permissions:**
    - **Admin lawyers:** Full access to all change logs
    - **Regular lawyers:** Access to change logs for records they can access
    
    **Filtering & Search:**
    - Filter by: model_name, change_type, changed_by, object_id, field_name
    - Date range filtering with changed_at_from and changed_at_to
    - Search by: field_name, changed_by email
    - Order by: changed_at, change_type, model_name
    
    **Available Actions:**
    - `GET /api/change-logs/` - List all change logs (permissions apply)
    - `GET /api/change-logs/{id}/` - Retrieve change log details
    - `GET /api/change-logs/client-changes/` - Get only client changes
    - `GET /api/change-logs/mandate-changes/` - Get only mandate changes
    - `GET /api/change-logs/timeentry-changes/` - Get only time entry changes
    - `GET /api/change-logs/recent/` - Get recent changes (last 24 hours)
    - `GET /api/change-logs/user-activity/` - Get changes by specific user
    
    **Query Parameters:**
    - `model_name` - Filter by model type (client, mandate, timeentry)
    - `change_type` - Filter by change type (CREATE, UPDATE, DELETE)
    - `changed_by` - Filter by user ID
    - `object_id` - Filter by specific object ID
    - `field_name` - Filter by specific field name
    - `changed_at_from` - Filter changes from date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    - `changed_at_to` - Filter changes to date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
    - `search` - Search in field names and user emails
    """
    
    queryset = ChangeLog.objects.all()
    serializer_class = ChangeLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['change_type', 'changed_by', 'object_id', 'field_name']
    search_fields = ['field_name', 'changed_by__email', 'changed_by__first_name', 'changed_by__last_name']
    ordering_fields = ['changed_at', 'change_type']
    ordering = ['-changed_at']
    
    def get_queryset(self):
        """Filter change logs based on user permissions."""
        queryset = ChangeLog.objects.all()
        user = self.request.user
        
        # Admin lawyers can see all change logs
        if user.is_admin_lawyer:
            queryset = queryset
        else:
            # Regular lawyers can only see change logs for records they can access
            # Get content types for tracked models
            client_ct = ContentType.objects.get_for_model(Client)
            mandate_ct = ContentType.objects.get_for_model(Mandate)
            timeentry_ct = ContentType.objects.get_for_model(TimeEntry)
            
            # Build permission filter
            accessible_changes = Q()
            
            # Client changes - all users can see (per ClientViewSet permissions)
            accessible_changes |= Q(content_type=client_ct)
            
            # Mandate changes - only for mandates they're assigned to
            if user.lawyer_profile:
                accessible_mandate_ids = user.lawyer_profile.mandates.values_list('id', flat=True)
                accessible_changes |= Q(
                    content_type=mandate_ct,
                    object_id__in=accessible_mandate_ids
                )
                
                # Time entry changes - only their own
                accessible_timeentry_ids = user.lawyer_profile.time_entries.values_list('id', flat=True)
                accessible_changes |= Q(
                    content_type=timeentry_ct,
                    object_id__in=accessible_timeentry_ids
                )
            
            queryset = queryset.filter(accessible_changes)
        
        # Apply date range filtering
        changed_at_from = self.request.query_params.get('changed_at_from')
        changed_at_to = self.request.query_params.get('changed_at_to')
        
        if changed_at_from:
            try:
                # Try to parse as datetime first, then as date
                if ' ' in changed_at_from:
                    from_date = datetime.strptime(changed_at_from, '%Y-%m-%d %H:%M:%S')
                else:
                    from_date = datetime.strptime(changed_at_from, '%Y-%m-%d')
                
                # Make timezone aware
                from_date = timezone.make_aware(from_date)
                queryset = queryset.filter(changed_at__gte=from_date)
            except ValueError:
                pass  # Invalid date format, ignore
        
        if changed_at_to:
            try:
                # Try to parse as datetime first, then as date
                if ' ' in changed_at_to:
                    to_date = datetime.strptime(changed_at_to, '%Y-%m-%d %H:%M:%S')
                else:
                    to_date = datetime.strptime(changed_at_to, '%Y-%m-%d')
                    # If only date provided, include the whole day
                    to_date = to_date.replace(hour=23, minute=59, second=59)
                
                # Make timezone aware
                to_date = timezone.make_aware(to_date)
                queryset = queryset.filter(changed_at__lte=to_date)
            except ValueError:
                pass  # Invalid date format, ignore
        
        return queryset
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve, list serializer for list."""
        if self.action == 'retrieve':
            return ChangeLogSerializer
        return ChangeLogListSerializer
    
    @action(detail=False, methods=['get'])
    def client_changes(self, request):
        """Get change logs for client model only."""
        client_ct = ContentType.objects.get_for_model(Client)
        queryset = self.get_queryset().filter(content_type=client_ct)
        
        # Apply filtering and pagination
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mandate_changes(self, request):
        """Get change logs for mandate model only."""
        mandate_ct = ContentType.objects.get_for_model(Mandate)
        queryset = self.get_queryset().filter(content_type=mandate_ct)
        
        # Apply filtering and pagination
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def timeentry_changes(self, request):
        """Get change logs for time entry model only."""
        timeentry_ct = ContentType.objects.get_for_model(TimeEntry)
        queryset = self.get_queryset().filter(content_type=timeentry_ct)
        
        # Apply filtering and pagination
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent changes (last 24 hours)."""
        since = timezone.now() - timedelta(hours=24)
        queryset = self.get_queryset().filter(changed_at__gte=since)
        
        # Apply filtering and pagination
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """
        Get changes by specific user.
        
        Query parameter:
        - user_id: ID of the user whose activity to show
        """
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response({'error': 'user_id parameter is required'}, status=400)
        
        try:
            user_id = int(user_id)
        except ValueError:
            return Response({'error': 'user_id must be an integer'}, status=400)
        
        queryset = self.get_queryset().filter(changed_by_id=user_id)
        
        # Apply filtering and pagination
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def object_history(self, request):
        """
        Get change history for a specific object.
        
        Query parameters:
        - model_name: Name of the model (client, mandate, timeentry)
        - object_id: ID of the object
        """
        model_name = request.query_params.get('model_name')
        object_id = request.query_params.get('object_id')
        
        if not model_name or not object_id:
            return Response({
                'error': 'model_name and object_id parameters are required'
            }, status=400)
        
        # Validate model name
        model_mapping = {
            'client': Client,
            'mandate': Mandate,
            'timeentry': TimeEntry
        }
        
        if model_name not in model_mapping:
            return Response({
                'error': f'Invalid model_name. Must be one of: {", ".join(model_mapping.keys())}'
            }, status=400)
        
        try:
            object_id = int(object_id)
        except ValueError:
            return Response({'error': 'object_id must be an integer'}, status=400)
        
        # Get content type and filter changes
        model_class = model_mapping[model_name]
        content_type = ContentType.objects.get_for_model(model_class)
        
        queryset = self.get_queryset().filter(
            content_type=content_type,
            object_id=object_id
        )
        
        # Apply filtering and pagination
        filtered_queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(filtered_queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(filtered_queryset, many=True)
        return Response(serializer.data)