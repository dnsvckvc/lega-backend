from rest_framework import permissions


class IsAdminLawyer(permissions.BasePermission):
    """
    Custom permission to only allow admin lawyers to access certain views.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin_lawyer
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to allow users to access their own data or admins to access all data.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin lawyers can access everything
        if request.user.is_admin_lawyer:
            return True
        
        # Check if the object has a user relationship
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Check if the object has a lawyer relationship and user is linked to that lawyer
        if hasattr(obj, 'lawyer') and request.user.lawyer_profile:
            return obj.lawyer == request.user.lawyer_profile
        
        return False


class CanAccessMandate(permissions.BasePermission):
    """
    Custom permission for mandate access based on user role and assignment.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return request.user.can_access_mandate(obj)


class CanAccessTimeEntry(permissions.BasePermission):
    """
    Custom permission for time entry access based on user role and ownership.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        return request.user.can_access_time_entry(obj)


class CanModifyMandate(permissions.BasePermission):
    """
    Permission for mandate modification.
    Admin lawyers can modify all mandates.
    Regular lawyers can only modify mandates they're assigned to (limited fields).
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_lawyer:
            return True
        
        # Regular lawyers can only update certain fields of their assigned mandates
        if request.method in ['PUT', 'PATCH']:
            if request.user.can_access_mandate(obj):
                # Check if only allowed fields are being modified
                allowed_fields = ['description', 'status']
                if request.data:
                    modified_fields = set(request.data.keys())
                    if not modified_fields.issubset(allowed_fields):
                        return False
                return True
        
        return request.user.can_access_mandate(obj)


class ReadOnlyOrAdmin(permissions.BasePermission):
    """
    Permission that allows read access to all authenticated users,
    but write access only to admin lawyers.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admin lawyers
        return request.user.is_admin_lawyer