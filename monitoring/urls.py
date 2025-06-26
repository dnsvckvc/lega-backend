"""
URL patterns for monitoring dashboard.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_stats, name='monitoring-dashboard'),
    path('logs/', views.recent_logs, name='monitoring-logs'),
    path('activity/', views.user_activity, name='monitoring-activity'),
    path('health/', views.system_health, name='monitoring-health'),
]