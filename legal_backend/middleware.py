"""
Custom middleware for logging and monitoring.
"""

import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.contrib.auth.models import AnonymousUser

# Initialize loggers
performance_logger = logging.getLogger('legal_backend.performance')
api_logger = logging.getLogger('legal_backend.api')
audit_logger = logging.getLogger('legal_backend.audit')


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware to monitor API performance and log slow requests.
    """

    def process_request(self, request):
        request.start_time = time.time()
        request.url_name = None
        
        # Get URL name for better logging
        try:
            resolved = resolve(request.path_info)
            request.url_name = resolved.url_name or resolved.view_name
        except:
            request.url_name = 'unknown'

    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log performance metrics
            self.log_performance_metrics(request, response, duration)
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                performance_logger.warning(
                    f"SLOW_REQUEST | {request.method} {request.path} | "
                    f"Duration: {duration:.3f}s | User: {getattr(request.user, 'email', 'anonymous')} | "
                    f"Status: {response.status_code}"
                )
            
            # Add performance header for debugging
            response['X-Response-Time'] = f'{duration:.3f}s'
        
        return response

    def log_performance_metrics(self, request, response, duration):
        """Log detailed performance metrics."""
        user_info = 'anonymous'
        user_role = 'anonymous'
        
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            user_info = request.user.email
            user_role = getattr(request.user, 'role', 'unknown')
        
        performance_logger.info(
            f"REQUEST | {request.method} {request.path} | "
            f"URL: {request.url_name} | "
            f"Duration: {duration:.3f}s | "
            f"Status: {response.status_code} | "
            f"User: {user_info} | "
            f"Role: {user_role} | "
            f"IP: {self.get_client_ip(request)} | "
            f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')[:100]}"
        )

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log API requests and responses for audit purposes.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Skip logging for these paths
        self.skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]

    def __call__(self, request):
        # Skip certain paths
        if any(request.path.startswith(path) for path in self.skip_paths):
            return self.get_response(request)

        # Log request
        self.log_request(request)
        
        response = self.get_response(request)
        
        # Log response
        self.log_response(request, response)
        
        return response

    def log_request(self, request):
        """Log incoming API requests."""
        user_info = 'anonymous'
        user_role = 'anonymous'
        
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            user_info = request.user.email
            user_role = getattr(request.user, 'role', 'unknown')

        # Log request details
        log_data = {
            'type': 'REQUEST',
            'method': request.method,
            'path': request.path,
            'user': user_info,
            'role': user_role,
            'ip': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')[:200],
        }

        # Add query parameters if present
        if request.GET:
            log_data['query_params'] = dict(request.GET)

        # Add request body for POST/PUT/PATCH (excluding sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                body = json.loads(request.body.decode('utf-8'))
                # Remove sensitive fields
                sanitized_body = self.sanitize_data(body)
                log_data['body'] = sanitized_body
            except (json.JSONDecodeError, UnicodeDecodeError):
                log_data['body'] = 'Invalid JSON or encoding'

        api_logger.info(self.format_log_message(log_data))

    def log_response(self, request, response):
        """Log API responses."""
        user_info = 'anonymous'
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            user_info = request.user.email

        log_data = {
            'type': 'RESPONSE',
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'user': user_info,
        }

        # Log response body for errors
        if response.status_code >= 400:
            try:
                if hasattr(response, 'data'):
                    log_data['response_body'] = response.data
                elif hasattr(response, 'content'):
                    content = response.content.decode('utf-8')
                    if content:
                        log_data['response_body'] = content[:1000]  # Limit size
            except:
                log_data['response_body'] = 'Unable to decode response'

        api_logger.info(self.format_log_message(log_data))

    def sanitize_data(self, data):
        """Remove sensitive information from request data."""
        sensitive_fields = ['password', 'token', 'secret', 'key', 'refresh']
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    sanitized[key] = '***REDACTED***'
                elif isinstance(value, dict):
                    sanitized[key] = self.sanitize_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [self.sanitize_data(item) if isinstance(item, dict) else item for item in value]
                else:
                    sanitized[key] = value
            return sanitized
        
        return data

    def format_log_message(self, data):
        """Format log data as a readable string."""
        return ' | '.join([f"{key}: {value}" for key, value in data.items()])

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AuditTrailMiddleware(MiddlewareMixin):
    """
    Middleware to create audit trails for important actions.
    """

    def process_response(self, request, response):
        # Only audit successful API operations that modify data
        if (request.path.startswith('/api/') and 
            request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and
            response.status_code in [200, 201, 204]):
            
            self.log_audit_trail(request, response)
        
        return response

    def log_audit_trail(self, request, response):
        """Log audit trail for data modification operations."""
        user_info = 'anonymous'
        user_role = 'anonymous'
        
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            user_info = request.user.email
            user_role = getattr(request.user, 'role', 'unknown')

        # Extract resource information from URL
        path_parts = request.path.strip('/').split('/')
        resource_type = 'unknown'
        resource_id = 'unknown'
        
        if len(path_parts) >= 2:
            resource_type = path_parts[1]  # e.g., 'clients', 'mandates'
            
        if len(path_parts) >= 3 and path_parts[2].isdigit():
            resource_id = path_parts[2]

        action_map = {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE'
        }
        
        action = action_map.get(request.method, 'UNKNOWN')

        audit_logger.info(
            f"AUDIT | Action: {action} | "
            f"Resource: {resource_type} | "
            f"ID: {resource_id} | "
            f"User: {user_info} | "
            f"Role: {user_role} | "
            f"IP: {self.get_client_ip(request)} | "
            f"Status: {response.status_code} | "
            f"Path: {request.path}"
        )

    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip