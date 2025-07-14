"""
Change tracking service for logging model changes.
"""

import json
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from .models import ChangeLog, Client, Mandate, TimeEntry


class ChangeTracker:
    """
    Service class to handle change tracking for models.
    """
    
    # Define which models we want to track
    TRACKED_MODELS = [Client, Mandate, TimeEntry]
    
    # Fields to exclude from tracking (sensitive or unimportant fields)
    EXCLUDED_FIELDS = {
        'created_at', 'updated_at', 'id', 'password', 'last_login'
    }
    
    @classmethod
    def log_change(cls, instance, field_name, old_value, new_value, change_type, user, request=None):
        """
        Log a single field change.
        
        Args:
            instance: The model instance that changed
            field_name: Name of the field that changed
            old_value: Previous value
            new_value: New value
            change_type: Type of change ('CREATE', 'UPDATE', 'DELETE')
            user: User who made the change
            request: HTTP request object (for IP and user agent)
        """
        # Only track changes for configured models
        if not any(isinstance(instance, model) for model in cls.TRACKED_MODELS):
            return
            
        # Skip excluded fields
        if field_name in cls.EXCLUDED_FIELDS:
            return
        
        # Get content type for the model
        content_type = ContentType.objects.get_for_model(instance)
        
        # Serialize values to JSON
        old_value_json = cls._serialize_value(old_value)
        new_value_json = cls._serialize_value(new_value)
        
        # Extract request metadata
        ip_address = None
        user_agent = None
        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
        
        # Create change log entry
        ChangeLog.objects.create(
            content_type=content_type,
            object_id=instance.pk,
            field_name=field_name,
            old_value=old_value_json,
            new_value=new_value_json,
            change_type=change_type,
            changed_by=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_model_changes(cls, instance, changes, change_type, user, request=None):
        """
        Log multiple field changes for a model instance.
        
        Args:
            instance: The model instance that changed
            changes: Dict of field_name -> (old_value, new_value)
            change_type: Type of change ('CREATE', 'UPDATE', 'DELETE')
            user: User who made the change
            request: HTTP request object (for IP and user agent)
        """
        for field_name, (old_value, new_value) in changes.items():
            cls.log_change(instance, field_name, old_value, new_value, change_type, user, request)
    
    @classmethod
    def track_model_update(cls, instance, old_instance, user, request=None):
        """
        Compare old and new instance values and log changes.
        
        Args:
            instance: New model instance
            old_instance: Previous model instance
            user: User who made the change
            request: HTTP request object
        """
        changes = {}
        
        # Get all fields for the model
        for field in instance._meta.fields:
            field_name = field.name
            
            # Skip excluded fields
            if field_name in cls.EXCLUDED_FIELDS:
                continue
            
            old_value = getattr(old_instance, field_name, None)
            new_value = getattr(instance, field_name, None)
            
            # Only log if value actually changed
            if old_value != new_value:
                changes[field_name] = (old_value, new_value)
        
        # Log all changes
        if changes:
            cls.log_model_changes(instance, changes, 'UPDATE', user, request)
    
    @classmethod
    def track_model_creation(cls, instance, user, request=None):
        """
        Track creation of a new model instance.
        
        Args:
            instance: New model instance
            user: User who created the instance
            request: HTTP request object
        """
        changes = {}
        
        # For creation, old_value is None, new_value is the current value
        for field in instance._meta.fields:
            field_name = field.name
            
            # Skip excluded fields
            if field_name in cls.EXCLUDED_FIELDS:
                continue
            
            new_value = getattr(instance, field_name, None)
            if new_value is not None:  # Only log fields with values
                changes[field_name] = (None, new_value)
        
        # Log all changes
        if changes:
            cls.log_model_changes(instance, changes, 'CREATE', user, request)
    
    @classmethod
    def track_model_deletion(cls, instance, user, request=None):
        """
        Track deletion of a model instance.
        
        Args:
            instance: Model instance being deleted
            user: User who deleted the instance
            request: HTTP request object
        """
        changes = {}
        
        # For deletion, new_value is None, old_value is the current value
        for field in instance._meta.fields:
            field_name = field.name
            
            # Skip excluded fields
            if field_name in cls.EXCLUDED_FIELDS:
                continue
            
            old_value = getattr(instance, field_name, None)
            if old_value is not None:  # Only log fields with values
                changes[field_name] = (old_value, None)
        
        # Log all changes
        if changes:
            cls.log_model_changes(instance, changes, 'DELETE', user, request)
    
    @classmethod
    def _serialize_value(cls, value):
        """
        Serialize a value to JSON string.
        
        Args:
            value: Value to serialize
            
        Returns:
            JSON string representation of the value
        """
        try:
            return json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False)
        except (TypeError, ValueError):
            # If serialization fails, convert to string
            return str(value) if value is not None else None
    
    @classmethod
    def _get_client_ip(cls, request):
        """
        Get client IP address from request.
        
        Args:
            request: HTTP request object
            
        Returns:
            Client IP address as string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip