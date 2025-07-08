from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAuthenticatedOrDocsAccess(BasePermission):
    """
    Custom permission that allows public access to documentation
    while requiring authentication for all other endpoints.
    """
    
    def has_permission(self, request, view):
        # Allow public access to documentation URLs
        if request.path.startswith('/docs/'):
            return True
        
        # For all other endpoints, require authentication
        return IsAuthenticated().has_permission(request, view)