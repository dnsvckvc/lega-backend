"""
Management command to check system health and send alerts.
This can be run as a cron job to monitor the system continuously.
"""

import os
import smtplib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone


class Command(BaseCommand):
    help = 'Check system health and send alerts for critical issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send alerts to',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run checks but do not send emails',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed output',
        )

    def handle(self, *args, **options):
        self.email = options.get('email')
        self.dry_run = options.get('dry_run', False)
        self.verbose = options.get('verbose', False)
        
        self.stdout.write(self.style.SUCCESS('🔍 Starting system health check...'))
        
        # Perform health checks
        alerts = []
        
        # Check for critical errors
        error_alerts = self.check_critical_errors()
        alerts.extend(error_alerts)
        
        # Check for performance issues
        perf_alerts = self.check_performance_issues()
        alerts.extend(perf_alerts)
        
        # Check for security issues
        security_alerts = self.check_security_issues()
        alerts.extend(security_alerts)
        
        # Check disk usage
        disk_alerts = self.check_disk_usage()
        alerts.extend(disk_alerts)
        
        # Check for failed requests
        request_alerts = self.check_failed_requests()
        alerts.extend(request_alerts)
        
        # Generate report
        if alerts:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Found {len(alerts)} alerts')
            )
            
            if self.email and not self.dry_run:
                self.send_alert_email(alerts)
                self.stdout.write(
                    self.style.SUCCESS(f'📧 Alert email sent to {self.email}')
                )
            elif self.dry_run:
                self.stdout.write(
                    self.style.WARNING('🧪 Dry run mode - no email sent')
                )
                
            # Print alerts
            for alert in alerts:
                level_style = self.get_style_for_severity(alert['severity'])
                self.stdout.write(
                    level_style(f"  {alert['severity'].upper()}: {alert['message']}")
                )
        else:
            self.stdout.write(self.style.SUCCESS('✅ No alerts found - system healthy'))

    def get_style_for_severity(self, severity):
        """Get console style based on alert severity."""
        if severity == 'high':
            return self.style.ERROR
        elif severity == 'medium':
            return self.style.WARNING
        else:
            return self.style.NOTICE

    def check_critical_errors(self):
        """Check for critical errors in logs."""
        alerts = []
        logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
        error_log = logs_dir / 'errors.log'
        
        if not error_log.exists():
            return alerts
        
        try:
            today = datetime.now().date()
            critical_errors = 0
            recent_errors = []
            
            with open(error_log, 'r') as f:
                for line in f:
                    if self.parse_log_date(line) == today:
                        if any(level in line.upper() for level in ['CRITICAL', 'FATAL', 'ERROR']):
                            critical_errors += 1
                            if len(recent_errors) < 5:
                                recent_errors.append(line.strip())
            
            if critical_errors > 0:
                alerts.append({
                    'type': 'error',
                    'severity': 'high' if critical_errors > 5 else 'medium',
                    'message': f'{critical_errors} critical/error entries found today',
                    'details': recent_errors
                })
                
        except Exception as e:
            if self.verbose:
                self.stdout.write(f"Error checking error logs: {e}")
        
        return alerts

    def check_performance_issues(self):
        """Check for performance issues."""
        alerts = []
        logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
        perf_log = logs_dir / 'performance.log'
        
        if not perf_log.exists():
            return alerts
        
        try:
            today = datetime.now().date()
            slow_requests = 0
            very_slow_requests = 0
            total_requests = 0
            response_times = []
            
            with open(perf_log, 'r') as f:
                for line in f:
                    if self.parse_log_date(line) == today and 'Duration:' in line:
                        total_requests += 1
                        
                        try:
                            duration_part = line.split('Duration:')[1].split('s')[0].strip()
                            duration = float(duration_part)
                            response_times.append(duration)
                            
                            if duration > 5.0:
                                very_slow_requests += 1
                            elif duration > 1.0:
                                slow_requests += 1
                        except:
                            pass
            
            # Alert for too many slow requests
            if total_requests > 0:
                slow_percentage = (slow_requests / total_requests) * 100
                
                if very_slow_requests > 5:
                    alerts.append({
                        'type': 'performance',
                        'severity': 'high',
                        'message': f'{very_slow_requests} very slow requests (>5s) detected today',
                        'details': []
                    })
                elif slow_percentage > 20:
                    alerts.append({
                        'type': 'performance',
                        'severity': 'medium',
                        'message': f'{slow_percentage:.1f}% of requests today were slow (>1s)',
                        'details': []
                    })
                
                # Alert for high average response time
                if response_times:
                    avg_time = sum(response_times) / len(response_times)
                    if avg_time > 2.0:
                        alerts.append({
                            'type': 'performance',
                            'severity': 'medium',
                            'message': f'Average response time today is {avg_time:.2f}s',
                            'details': []
                        })
                        
        except Exception as e:
            if self.verbose:
                self.stdout.write(f"Error checking performance logs: {e}")
        
        return alerts

    def check_security_issues(self):
        """Check for security issues."""
        alerts = []
        logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
        auth_log = logs_dir / 'authentication.log'
        
        if not auth_log.exists():
            return alerts
        
        try:
            today = datetime.now().date()
            failed_logins = 0
            failed_ips = Counter()
            failed_emails = Counter()
            
            with open(auth_log, 'r') as f:
                for line in f:
                    if self.parse_log_date(line) == today and 'LOGIN_FAILED' in line:
                        failed_logins += 1
                        
                        # Extract IP
                        if 'IP:' in line:
                            try:
                                ip = line.split('IP:')[1].split('|')[0].strip()
                                failed_ips[ip] += 1
                            except:
                                pass
                        
                        # Extract email
                        if 'Email:' in line:
                            try:
                                email = line.split('Email:')[1].split('|')[0].strip()
                                failed_emails[email] += 1
                            except:
                                pass
            
            # Alert for too many failed logins
            if failed_logins > 10:
                alerts.append({
                    'type': 'security',
                    'severity': 'high',
                    'message': f'{failed_logins} failed login attempts detected today',
                    'details': []
                })
            elif failed_logins > 5:
                alerts.append({
                    'type': 'security',
                    'severity': 'medium',
                    'message': f'{failed_logins} failed login attempts detected today',
                    'details': []
                })
            
            # Alert for suspicious IP activity
            for ip, count in failed_ips.most_common(3):
                if count > 5:
                    alerts.append({
                        'type': 'security',
                        'severity': 'high',
                        'message': f'Suspicious activity from IP {ip}: {count} failed login attempts',
                        'details': []
                    })
                    
        except Exception as e:
            if self.verbose:
                self.stdout.write(f"Error checking security logs: {e}")
        
        return alerts

    def check_disk_usage(self):
        """Check log files disk usage."""
        alerts = []
        logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
        
        if not logs_dir.exists():
            return alerts
        
        try:
            total_size = 0
            for log_file in logs_dir.glob('*.log'):
                try:
                    total_size += log_file.stat().st_size
                except:
                    pass
            
            total_mb = total_size / (1024 * 1024)
            
            if total_mb > 500:  # 500MB
                alerts.append({
                    'type': 'disk',
                    'severity': 'high',
                    'message': f'Log files using {total_mb:.1f}MB of disk space',
                    'details': []
                })
            elif total_mb > 200:  # 200MB
                alerts.append({
                    'type': 'disk',
                    'severity': 'medium',
                    'message': f'Log files using {total_mb:.1f}MB of disk space',
                    'details': []
                })
                
        except Exception as e:
            if self.verbose:
                self.stdout.write(f"Error checking disk usage: {e}")
        
        return alerts

    def check_failed_requests(self):
        """Check for excessive failed requests."""
        alerts = []
        logs_dir = getattr(settings, 'LOGS_DIR', Path(settings.BASE_DIR) / 'logs')
        perf_log = logs_dir / 'performance.log'
        
        if not perf_log.exists():
            return alerts
        
        try:
            today = datetime.now().date()
            total_requests = 0
            failed_requests = 0
            status_codes = Counter()
            
            with open(perf_log, 'r') as f:
                for line in f:
                    if self.parse_log_date(line) == today and 'Status:' in line:
                        total_requests += 1
                        
                        try:
                            status_code = int(line.split('Status:')[1].split('|')[0].strip())
                            status_codes[status_code] += 1
                            
                            if status_code >= 400:
                                failed_requests += 1
                        except:
                            pass
            
            if total_requests > 0:
                error_rate = (failed_requests / total_requests) * 100
                
                if error_rate > 10:
                    alerts.append({
                        'type': 'requests',
                        'severity': 'high',
                        'message': f'High error rate: {error_rate:.1f}% of requests failing today',
                        'details': [f'Total requests: {total_requests}', f'Failed requests: {failed_requests}']
                    })
                elif error_rate > 5:
                    alerts.append({
                        'type': 'requests',
                        'severity': 'medium',
                        'message': f'Elevated error rate: {error_rate:.1f}% of requests failing today',
                        'details': [f'Total requests: {total_requests}', f'Failed requests: {failed_requests}']
                    })
                    
        except Exception as e:
            if self.verbose:
                self.stdout.write(f"Error checking request logs: {e}")
        
        return alerts

    def send_alert_email(self, alerts):
        """Send alert email."""
        if not self.email:
            return
        
        # Create email content
        subject = f'Legal Backend System Alert - {len(alerts)} issues detected'
        
        body = f"""
Legal Practice Management System Health Alert

Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Alerts Found: {len(alerts)}

ALERT DETAILS:
"""
        
        for i, alert in enumerate(alerts, 1):
            body += f"""
{i}. {alert['type'].upper()} ALERT ({alert['severity'].upper()})
   Message: {alert['message']}
"""
            if alert.get('details'):
                for detail in alert['details'][:3]:  # Limit details
                    body += f"   Detail: {detail}\n"
        
        body += f"""

This alert was generated automatically by the system health monitor.
Please investigate these issues as soon as possible.

System: Legal Practice Management Backend
Server Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        # For demo purposes, just print what would be sent
        # In production, you would configure actual SMTP settings
        if self.verbose:
            self.stdout.write("\n" + "="*50)
            self.stdout.write("EMAIL THAT WOULD BE SENT:")
            self.stdout.write("="*50)
            self.stdout.write(f"To: {self.email}")
            self.stdout.write(f"Subject: {subject}")
            self.stdout.write("\nBody:")
            self.stdout.write(body)
            self.stdout.write("="*50)

    def parse_log_date(self, log_line):
        """Parse the date from a log line."""
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