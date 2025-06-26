"""
Monitoring and logging dashboard views.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from authentication.permissions import IsAdminLawyer


@api_view(['GET'])
@permission_classes([IsAdminLawyer])
def dashboard_stats(request):
    """
    Get overall dashboard statistics for the monitoring system.
    """
    logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
    
    stats = {
        'total_requests_today': 0,
        'failed_requests_today': 0,
        'unique_users_today': set(),
        'avg_response_time': 0,
        'slow_requests_today': 0,
        'login_attempts_today': 0,
        'failed_logins_today': 0,
        'total_log_files': 0,
        'log_files_sizes': {},
        'last_updated': timezone.now().isoformat(),
    }
    
    try:
        # Check if logs directory exists
        if not logs_dir.exists():
            return Response({
                'error': 'Logs directory not found',
                'stats': stats
            })
        
        # Count log files and their sizes
        for log_file in logs_dir.glob('*.log'):
            stats['total_log_files'] += 1
            try:
                size = log_file.stat().st_size
                stats['log_files_sizes'][log_file.name] = {
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2)
                }
            except:
                stats['log_files_sizes'][log_file.name] = {'size_bytes': 0, 'size_mb': 0}
        
        # Parse performance logs for today's stats
        performance_log = logs_dir / 'performance.log'
        if performance_log.exists():
            today = datetime.now().date()
            response_times = []
            
            try:
                with open(performance_log, 'r') as f:
                    for line in f:
                        if parse_log_date(line) == today:
                            if 'REQUEST |' in line:
                                stats['total_requests_today'] += 1
                                
                                # Extract user
                                if 'User:' in line:
                                    user_part = line.split('User:')[1].split('|')[0].strip()
                                    if user_part != 'anonymous':
                                        stats['unique_users_today'].add(user_part)
                                
                                # Extract response time
                                if 'Duration:' in line:
                                    try:
                                        duration_part = line.split('Duration:')[1].split('s')[0].strip()
                                        duration = float(duration_part)
                                        response_times.append(duration)
                                        
                                        if duration > 1.0:
                                            stats['slow_requests_today'] += 1
                                    except:
                                        pass
                                
                                # Check for failed requests
                                if 'Status:' in line:
                                    try:
                                        status_part = line.split('Status:')[1].split('|')[0].strip()
                                        status_code = int(status_part)
                                        if status_code >= 400:
                                            stats['failed_requests_today'] += 1
                                    except:
                                        pass
            
            except Exception as e:
                pass
            
            # Calculate average response time
            if response_times:
                stats['avg_response_time'] = round(sum(response_times) / len(response_times), 3)
        
        # Parse authentication logs for login stats
        auth_log = logs_dir / 'authentication.log'
        if auth_log.exists():
            today = datetime.now().date()
            
            try:
                with open(auth_log, 'r') as f:
                    for line in f:
                        if parse_log_date(line) == today:
                            if 'LOGIN_SUCCESS' in line or 'Action: LOGIN' in line:
                                stats['login_attempts_today'] += 1
                            elif 'LOGIN_FAILED' in line:
                                stats['login_attempts_today'] += 1
                                stats['failed_logins_today'] += 1
            except Exception as e:
                pass
        
        # Convert set to count
        stats['unique_users_today'] = len(stats['unique_users_today'])
        
    except Exception as e:
        return Response({
            'error': f'Error processing logs: {str(e)}',
            'stats': stats
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAdminLawyer])
def recent_logs(request):
    """
    Get recent log entries from various log files.
    """
    log_type = request.GET.get('type', 'audit')  # audit, auth, performance, api, error
    limit = min(int(request.GET.get('limit', 50)), 200)  # Max 200 entries
    
    logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
    
    log_files = {
        'audit': 'audit.log',
        'auth': 'authentication.log',
        'performance': 'performance.log',
        'api': 'api_requests.log',
        'error': 'errors.log',
        'general': 'general.log'
    }
    
    if log_type not in log_files:
        return Response({
            'error': 'Invalid log type',
            'available_types': list(log_files.keys())
        }, status=status.HTTP_400_BAD_REQUEST)
    
    log_file = logs_dir / log_files[log_type]
    
    if not log_file.exists():
        return Response({
            'logs': [],
            'message': f'Log file {log_files[log_type]} not found'
        })
    
    try:
        logs = []
        with open(log_file, 'r') as f:
            # Read all lines and get the last 'limit' entries
            all_lines = f.readlines()
            recent_lines = all_lines[-limit:] if len(all_lines) > limit else all_lines
            
            for line in recent_lines:
                if line.strip():
                    parsed_log = parse_log_entry(line.strip())
                    if parsed_log:
                        logs.append(parsed_log)
        
        # Reverse to show newest first
        logs.reverse()
        
        return Response({
            'logs': logs,
            'count': len(logs),
            'log_type': log_type
        })
        
    except Exception as e:
        return Response({
            'error': f'Error reading log file: {str(e)}',
            'logs': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminLawyer])
def user_activity(request):
    """
    Get user activity statistics and recent actions.
    """
    days = min(int(request.GET.get('days', 7)), 30)  # Max 30 days
    user_email = request.GET.get('user')
    
    logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
    
    cutoff_date = datetime.now().date() - timedelta(days=days)
    
    activity_stats = {
        'date_range': {
            'from': cutoff_date.isoformat(),
            'to': datetime.now().date().isoformat(),
            'days': days
        },
        'user_stats': defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'logins': 0,
            'last_activity': None
        }),
        'daily_activity': defaultdict(lambda: {
            'total_requests': 0,
            'unique_users': set(),
            'logins': 0
        }),
        'top_endpoints': Counter(),
        'recent_actions': []
    }
    
    try:
        # Parse performance logs for user activity
        performance_log = logs_dir / 'performance.log'
        if performance_log.exists():
            with open(performance_log, 'r') as f:
                for line in f:
                    log_date = parse_log_date(line)
                    if log_date and log_date >= cutoff_date:
                        if 'REQUEST |' in line:
                            # Extract user
                            user = 'anonymous'
                            if 'User:' in line:
                                try:
                                    user = line.split('User:')[1].split('|')[0].strip()
                                except:
                                    pass
                            
                            # Skip if filtering by user and doesn't match
                            if user_email and user != user_email:
                                continue
                            
                            # Extract endpoint
                            endpoint = 'unknown'
                            if 'URL:' in line:
                                try:
                                    endpoint = line.split('URL:')[1].split('|')[0].strip()
                                except:
                                    pass
                            
                            # Extract status
                            status_code = 200
                            if 'Status:' in line:
                                try:
                                    status_code = int(line.split('Status:')[1].split('|')[0].strip())
                                except:
                                    pass
                            
                            # Update stats
                            activity_stats['user_stats'][user]['total_requests'] += 1
                            if status_code < 400:
                                activity_stats['user_stats'][user]['successful_requests'] += 1
                            else:
                                activity_stats['user_stats'][user]['failed_requests'] += 1
                            
                            activity_stats['user_stats'][user]['last_activity'] = log_date.isoformat()
                            
                            # Daily stats
                            activity_stats['daily_activity'][log_date.isoformat()]['total_requests'] += 1
                            activity_stats['daily_activity'][log_date.isoformat()]['unique_users'].add(user)
                            
                            # Top endpoints
                            activity_stats['top_endpoints'][endpoint] += 1
        
        # Parse auth logs for login activity
        auth_log = logs_dir / 'authentication.log'
        if auth_log.exists():
            with open(auth_log, 'r') as f:
                for line in f:
                    log_date = parse_log_date(line)
                    if log_date and log_date >= cutoff_date:
                        if 'LOGIN_SUCCESS' in line or 'Action: LOGIN' in line:
                            user = 'unknown'
                            if 'User:' in line:
                                try:
                                    user = line.split('User:')[1].split('|')[0].strip()
                                except:
                                    pass
                            
                            if not user_email or user == user_email:
                                activity_stats['user_stats'][user]['logins'] += 1
                                activity_stats['daily_activity'][log_date.isoformat()]['logins'] += 1
        
        # Parse audit logs for recent actions
        audit_log = logs_dir / 'audit.log'
        if audit_log.exists():
            with open(audit_log, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-50:]  # Last 50 entries
                
                for line in recent_lines:
                    log_date = parse_log_date(line)
                    if log_date and log_date >= cutoff_date:
                        parsed_action = parse_log_entry(line.strip())
                        if parsed_action:
                            if not user_email or user_email in line:
                                activity_stats['recent_actions'].append(parsed_action)
        
        # Convert sets to counts in daily activity
        for date_str in activity_stats['daily_activity']:
            activity_stats['daily_activity'][date_str]['unique_users'] = len(
                activity_stats['daily_activity'][date_str]['unique_users']
            )
        
        # Convert defaultdict to regular dict and get top endpoints
        activity_stats['user_stats'] = dict(activity_stats['user_stats'])
        activity_stats['daily_activity'] = dict(activity_stats['daily_activity'])
        activity_stats['top_endpoints'] = dict(activity_stats['top_endpoints'].most_common(10))
        
        # Reverse recent actions to show newest first
        activity_stats['recent_actions'].reverse()
        
    except Exception as e:
        return Response({
            'error': f'Error processing activity logs: {str(e)}',
            'activity_stats': activity_stats
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response(activity_stats)


@api_view(['GET'])
@permission_classes([IsAdminLawyer])
def system_health(request):
    """
    Get system health metrics and alerts.
    """
    logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
    
    health_stats = {
        'status': 'healthy',
        'alerts': [],
        'disk_usage': {},
        'recent_errors': [],
        'performance_issues': [],
        'security_alerts': [],
        'timestamp': timezone.now().isoformat()
    }
    
    try:
        # Check disk usage for logs
        if logs_dir.exists():
            total_size = 0
            for log_file in logs_dir.glob('*.log'):
                try:
                    size = log_file.stat().st_size
                    total_size += size
                    health_stats['disk_usage'][log_file.name] = {
                        'size_mb': round(size / (1024 * 1024), 2)
                    }
                except:
                    pass
            
            health_stats['disk_usage']['total_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Alert if logs are taking too much space (>100MB)
            if total_size > 100 * 1024 * 1024:
                health_stats['alerts'].append({
                    'type': 'warning',
                    'message': f'Log files are using {health_stats["disk_usage"]["total_mb"]}MB of disk space',
                    'severity': 'medium'
                })
                health_stats['status'] = 'warning'
        
        # Check for recent errors
        error_log = logs_dir / 'errors.log'
        if error_log.exists():
            today = datetime.now().date()
            try:
                with open(error_log, 'r') as f:
                    all_lines = f.readlines()
                    recent_lines = all_lines[-20:]  # Last 20 errors
                    
                    for line in recent_lines:
                        log_date = parse_log_date(line)
                        if log_date and log_date >= today - timedelta(days=1):
                            parsed_error = parse_log_entry(line.strip())
                            if parsed_error:
                                health_stats['recent_errors'].append(parsed_error)
                                
                                # Create alert for critical errors
                                if 'CRITICAL' in line or 'FATAL' in line:
                                    health_stats['alerts'].append({
                                        'type': 'error',
                                        'message': f'Critical error detected: {parsed_error.get("message", "Unknown error")[:100]}',
                                        'severity': 'high'
                                    })
                                    health_stats['status'] = 'error'
            except:
                pass
        
        # Check for performance issues
        performance_log = logs_dir / 'performance.log'
        if performance_log.exists():
            today = datetime.now().date()
            slow_requests = 0
            
            try:
                with open(performance_log, 'r') as f:
                    for line in f:
                        log_date = parse_log_date(line)
                        if log_date == today and 'SLOW_REQUEST' in line:
                            slow_requests += 1
                            parsed_slow = parse_log_entry(line.strip())
                            if parsed_slow and len(health_stats['performance_issues']) < 10:
                                health_stats['performance_issues'].append(parsed_slow)
                
                if slow_requests > 10:
                    health_stats['alerts'].append({
                        'type': 'warning',
                        'message': f'{slow_requests} slow requests detected today',
                        'severity': 'medium'
                    })
                    if health_stats['status'] == 'healthy':
                        health_stats['status'] = 'warning'
            except:
                pass
        
        # Check for security alerts (failed logins, etc.)
        auth_log = logs_dir / 'authentication.log'
        if auth_log.exists():
            today = datetime.now().date()
            failed_logins = 0
            
            try:
                with open(auth_log, 'r') as f:
                    for line in f:
                        log_date = parse_log_date(line)
                        if log_date == today and 'LOGIN_FAILED' in line:
                            failed_logins += 1
                            parsed_fail = parse_log_entry(line.strip())
                            if parsed_fail and len(health_stats['security_alerts']) < 10:
                                health_stats['security_alerts'].append(parsed_fail)
                
                if failed_logins > 5:
                    health_stats['alerts'].append({
                        'type': 'warning',
                        'message': f'{failed_logins} failed login attempts detected today',
                        'severity': 'medium'
                    })
                    if health_stats['status'] == 'healthy':
                        health_stats['status'] = 'warning'
            except:
                pass
        
    except Exception as e:
        health_stats['status'] = 'error'
        health_stats['alerts'].append({
            'type': 'error',
            'message': f'Error checking system health: {str(e)}',
            'severity': 'high'
        })
    
    return Response(health_stats)


def parse_log_date(log_line):
    """
    Parse the date from a log line.
    """
    try:
        # Expected format: "2025-06-26 16:13:42,973"
        if '|' in log_line:
            date_part = log_line.split('|')[0].strip()
        else:
            date_part = log_line.split()[0] + ' ' + log_line.split()[1]
        
        # Extract just the date part
        date_str = date_part.split()[0]
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None


def parse_log_entry(log_line):
    """
    Parse a log entry into a structured format.
    """
    try:
        parts = log_line.split('|')
        if len(parts) < 2:
            return {
                'timestamp': 'unknown',
                'level': 'unknown',
                'message': log_line.strip()
            }
        
        timestamp_part = parts[0].strip()
        level_part = parts[1].strip() if len(parts) > 1 else 'INFO'
        
        entry = {
            'timestamp': timestamp_part,
            'level': level_part,
            'message': '|'.join(parts[2:]).strip() if len(parts) > 2 else log_line,
            'raw': log_line
        }
        
        # Extract additional fields if available
        if 'User:' in log_line:
            try:
                user_part = log_line.split('User:')[1].split('|')[0].strip()
                entry['user'] = user_part
            except:
                pass
        
        if 'IP:' in log_line:
            try:
                ip_part = log_line.split('IP:')[1].split('|')[0].strip()
                entry['ip'] = ip_part
            except:
                pass
        
        if 'Action:' in log_line:
            try:
                action_part = log_line.split('Action:')[1].split('|')[0].strip()
                entry['action'] = action_part
            except:
                pass
        
        return entry
    except:
        return {
            'timestamp': 'unknown',
            'level': 'unknown',
            'message': log_line.strip(),
            'raw': log_line
        }
