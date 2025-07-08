"""
API Documentation Views
Provides documentation endpoints for the Legal Practice Management API
"""

from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.urls import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_schema(request):
    """
    API Schema Overview
    
    Provides a comprehensive overview of all available API endpoints
    in the Legal Practice Management system.
    """
    base_url = f"{request.scheme}://{request.get_host()}"
    
    schema = {
        "title": "Legal Practice Management API",
        "version": "1.0.0",
        "description": "Comprehensive REST API for managing legal practice operations including clients, lawyers, mandates, time tracking, invoicing, and system monitoring.",
        "base_url": base_url,
        "authentication": {
            "type": "JWT Bearer Token",
            "login_endpoint": f"{base_url}/auth/login/",
            "header_format": "Authorization: Bearer <access_token>"
        },
        "endpoints": {
            "authentication": {
                "base_path": "/auth/",
                "endpoints": {
                    "POST /auth/login/": "Login and obtain JWT tokens",
                    "POST /auth/token/refresh/": "Refresh access token",
                    "POST /auth/logout/": "Logout and blacklist refresh token",
                    "GET /auth/current-user/": "Get current user profile",
                    "POST /auth/register/": "Register new user (admin only)",
                    "GET /auth/users/": "List all users (admin only)",
                    "POST /auth/link-lawyer/": "Link user to lawyer profile (admin only)"
                }
            },
            "clients": {
                "base_path": "/api/clients/",
                "permissions": "Read: All users, Write: Admin only",
                "endpoints": {
                    "GET /api/clients/": "List all clients (with search & filtering)",
                    "POST /api/clients/": "Create new client",
                    "GET /api/clients/{id}/": "Get client details",
                    "PUT/PATCH /api/clients/{id}/": "Update client",
                    "DELETE /api/clients/{id}/": "Delete client",
                    "GET /api/clients/{id}/mandates/": "Get client's mandates"
                },
                "filters": ["name", "email"],
                "search_fields": ["name", "email"],
                "ordering": ["name", "created_at"]
            },
            "lawyers": {
                "base_path": "/api/lawyers/",
                "permissions": "Read: All users, Write: Admin only",
                "endpoints": {
                    "GET /api/lawyers/": "List all lawyers (with search & filtering)",
                    "POST /api/lawyers/": "Create new lawyer",
                    "GET /api/lawyers/{id}/": "Get lawyer details",
                    "PUT/PATCH /api/lawyers/{id}/": "Update lawyer",
                    "DELETE /api/lawyers/{id}/": "Delete lawyer",
                    "GET /api/lawyers/{id}/mandates/": "Get lawyer's mandates",
                    "GET /api/lawyers/{id}/time_entries/": "Get lawyer's time entries",
                    "GET /api/lawyers/{id}/monthly_billing/": "Get monthly billing summary"
                },
                "filters": ["name", "email", "hourly_rate"],
                "search_fields": ["name", "email"],
                "ordering": ["name", "hourly_rate", "created_at"]
            },
            "mandates": {
                "base_path": "/api/mandates/",
                "permissions": "Admin: Full access, Regular: Assigned mandates only",
                "endpoints": {
                    "GET /api/mandates/": "List mandates (role-filtered)",
                    "POST /api/mandates/": "Create new mandate",
                    "GET /api/mandates/{id}/": "Get mandate details",
                    "PUT/PATCH /api/mandates/{id}/": "Update mandate",
                    "DELETE /api/mandates/{id}/": "Delete mandate",
                    "GET /api/mandates/{id}/summary/": "Get mandate cost summary",
                    "GET /api/mandates/{id}/time_entries/": "Get mandate's time entries"
                },
                "filters": ["client", "lawyers", "due_date", "status", "is_active"],
                "search_fields": ["name", "description", "client__name"],
                "ordering": ["name", "due_date", "created_at"],
                "special_filters": {
                    "status=active": "Only active mandates",
                    "status=inactive": "Only inactive mandates", 
                    "status=overdue": "Only overdue active mandates"
                }
            },
            "time_entries": {
                "base_path": "/api/time-entries/",
                "permissions": "Admin: All entries, Regular: Own entries only",
                "endpoints": {
                    "GET /api/time-entries/": "List time entries (role-filtered)",
                    "POST /api/time-entries/": "Create new time entry",
                    "GET /api/time-entries/{id}/": "Get time entry details",
                    "PUT/PATCH /api/time-entries/{id}/": "Update time entry",
                    "DELETE /api/time-entries/{id}/": "Delete time entry"
                },
                "filters": ["mandate", "lawyer", "date", "date_from", "date_to"],
                "search_fields": ["description", "mandate__name", "lawyer__name"],
                "ordering": ["date", "hours", "created_at"]
            },
            "invoices": {
                "base_path": "/api/invoices/",
                "permissions": "Authenticated lawyers",
                "endpoints": {
                    "GET /api/invoices/": "List invoices with filtering",
                    "POST /api/invoices/": "Create new invoice",
                    "GET /api/invoices/{id}/": "Get invoice details",
                    "PUT/PATCH /api/invoices/{id}/": "Update invoice",
                    "DELETE /api/invoices/{id}/": "Delete invoice",
                    "PATCH /api/invoices/{id}/update_status/": "Update invoice status",
                    "GET /api/invoices/{id}/download_pdf/": "Download invoice PDF",
                    "POST /api/invoices/generate_from_time_entries/": "Generate invoice from time entries",
                    "GET /api/invoices/summary/": "Get invoice summary statistics",
                    "GET /api/invoices/summary_pdf/": "Download summary PDF",
                    "POST /api/invoices/update_overdue_statuses/": "Update overdue statuses (admin)"
                },
                "filters": ["status", "client", "mandate", "issue_date_from", "issue_date_to", "due_date_from", "due_date_to", "overdue"],
                "search_fields": ["invoice_number", "client__name", "mandate__name"],
                "ordering": ["created_at", "issue_date", "due_date", "total_amount"]
            },
            "monitoring": {
                "base_path": "/monitoring/",
                "permissions": "Admin lawyers only",
                "endpoints": {
                    "GET /monitoring/dashboard/": "System dashboard statistics",
                    "GET /monitoring/logs/": "Recent system logs (with type filtering)",
                    "GET /monitoring/activity/": "User activity statistics",
                    "GET /monitoring/health/": "System health status and alerts"
                },
                "log_types": ["general", "error", "performance", "api", "auth", "audit"]
            }
        },
        "data_models": {
            "Client": {
                "fields": ["id", "name", "email", "phone", "address", "created_at", "updated_at"],
                "relationships": "Has many mandates"
            },
            "Lawyer": {
                "fields": ["id", "name", "email", "phone", "hourly_rate", "created_at", "updated_at"],
                "relationships": "Assigned to many mandates, has many time entries"
            },
            "Mandate": {
                "fields": ["id", "name", "description", "client", "lawyers", "due_date", "cost_ceiling", "is_active", "created_at", "updated_at"],
                "relationships": "Belongs to one client, assigned to many lawyers, has many time entries"
            },
            "TimeEntry": {
                "fields": ["id", "mandate", "lawyer", "date", "hours", "description", "is_billable", "is_invoiced", "cost", "created_at", "updated_at"],
                "relationships": "Belongs to one mandate and one lawyer"
            },
            "Invoice": {
                "fields": ["id", "invoice_number", "client", "mandate", "issue_date", "due_date", "status", "subtotal", "tax_rate", "tax_amount", "total_amount", "notes", "paid_date", "created_at", "updated_at"],
                "relationships": "Belongs to one client, optionally to one mandate, has many line items"
            }
        },
        "common_patterns": {
            "pagination": {
                "default_page_size": 20,
                "query_params": ["page", "page_size"]
            },
            "filtering": {
                "date_ranges": "Use date_from and date_to parameters",
                "search": "Use search parameter for text search",
                "ordering": "Use ordering parameter (prefix with - for descending)"
            },
            "authentication": {
                "header": "Authorization: Bearer <access_token>",
                "token_refresh": "Use refresh token at /auth/token/refresh/",
                "token_expiry": "Access tokens expire, refresh tokens have longer lifetime"
            }
        },
        "response_formats": {
            "success": {
                "status_codes": [200, 201, 204],
                "list_format": {
                    "count": "total number of items",
                    "next": "URL for next page or null",
                    "previous": "URL for previous page or null", 
                    "results": "array of objects"
                }
            },
            "errors": {
                "status_codes": [400, 401, 403, 404, 500],
                "format": {
                    "error": "error message",
                    "details": "detailed validation errors (if applicable)"
                }
            }
        }
    }
    
    return Response(schema)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_examples(request):
    """
    API Usage Examples
    
    Provides practical examples of how to use the API endpoints.
    """
    base_url = f"{request.scheme}://{request.get_host()}"
    
    examples = {
        "authentication_flow": {
            "1_login": {
                "method": "POST",
                "url": f"{base_url}/auth/login/",
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "email": "sarah.wilson@lawfirm.com",
                    "password": "admin123"
                },
                "response": {
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "user": {"id": 1, "email": "sarah.wilson@lawfirm.com", "role": "admin"}
                }
            },
            "2_use_token": {
                "method": "GET",
                "url": f"{base_url}/api/mandates/",
                "headers": {"Authorization": "Bearer <access_token>"},
                "description": "Use the access token for authenticated requests"
            },
            "3_refresh_token": {
                "method": "POST", 
                "url": f"{base_url}/auth/token/refresh/",
                "body": {"refresh": "<refresh_token>"},
                "description": "Refresh expired access token"
            }
        },
        "common_operations": {
            "create_client": {
                "method": "POST",
                "url": f"{base_url}/api/clients/",
                "headers": {
                    "Authorization": "Bearer <admin_token>",
                    "Content-Type": "application/json"
                },
                "body": {
                    "name": "New Tech Startup Inc.",
                    "email": "contact@newtechstartup.com", 
                    "phone": "555-0199",
                    "address": "456 Innovation Drive, Silicon Valley, CA"
                }
            },
            "create_mandate": {
                "method": "POST",
                "url": f"{base_url}/api/mandates/",
                "body": {
                    "name": "Corporate Merger Legal Review",
                    "description": "Legal due diligence for merger and acquisition",
                    "client": 1,
                    "lawyers": [1, 2],
                    "due_date": "2025-12-31",
                    "cost_ceiling": "50000.00",
                    "is_active": True
                }
            },
            "log_time_entry": {
                "method": "POST",
                "url": f"{base_url}/api/time-entries/",
                "body": {
                    "mandate": 1,
                    "lawyer": 1,
                    "date": "2025-07-08",
                    "hours": "3.5",
                    "description": "Contract review and client consultation",
                    "is_billable": True
                }
            },
            "generate_invoice": {
                "method": "POST",
                "url": f"{base_url}/api/invoices/generate_from_time_entries/",
                "body": {
                    "client_id": 1,
                    "start_date": "2025-07-01",
                    "end_date": "2025-07-31", 
                    "due_days": 30,
                    "tax_rate": "21.00",
                    "notes": "Monthly legal services"
                }
            }
        },
        "filtering_examples": {
            "search_clients": f"{base_url}/api/clients/?search=Tech",
            "filter_mandates_by_client": f"{base_url}/api/mandates/?client=1",
            "filter_overdue_mandates": f"{base_url}/api/mandates/?status=overdue",
            "filter_time_entries_by_date": f"{base_url}/api/time-entries/?date_from=2025-07-01&date_to=2025-07-31",
            "order_lawyers_by_rate": f"{base_url}/api/lawyers/?ordering=-hourly_rate",
            "paginate_results": f"{base_url}/api/time-entries/?page=2&page_size=10"
        },
        "monitoring_examples": {
            "system_dashboard": f"{base_url}/monitoring/dashboard/",
            "error_logs": f"{base_url}/monitoring/logs/?type=error&limit=25",
            "user_activity": f"{base_url}/monitoring/activity/?days=7",
            "system_health": f"{base_url}/monitoring/health/"
        }
    }
    
    return Response(examples)