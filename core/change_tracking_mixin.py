"""
Mixin for ViewSets to automatically track changes.
"""

from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from .change_tracker import ChangeTracker


class ChangeTrackingMixin:
    """
    Mixin to add change tracking to ViewSets.
    Automatically tracks CREATE, UPDATE, and DELETE operations.
    """
    
    def create(self, request, *args, **kwargs):
        """Override create to add change tracking."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Save the instance
            instance = serializer.save()
            
            # Track the creation
            ChangeTracker.track_model_creation(instance, request.user, request)
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        """Override update to add change tracking."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Create a copy of the old instance for comparison
        old_instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            # Save the updated instance
            updated_instance = serializer.save()
            
            # Track the changes
            ChangeTracker.track_model_update(updated_instance, old_instance, request.user, request)
            
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            
            return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to add change tracking."""
        instance = self.get_object()
        
        with transaction.atomic():
            # Track the deletion before actually deleting
            ChangeTracker.track_model_deletion(instance, request.user, request)
            
            # Delete the instance
            self.perform_destroy(instance)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    def perform_create(self, serializer):
        """Override if needed by subclasses."""
        serializer.save()
    
    def perform_update(self, serializer):
        """Override if needed by subclasses."""
        serializer.save()
    
    def perform_destroy(self, instance):
        """Override if needed by subclasses."""
        instance.delete()