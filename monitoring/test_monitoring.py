from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.management import call_command
from unittest.mock import patch, MagicMock
from io import StringIO
import json

from core.models import Lawyer, Client, Mandate, TimeEntry
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class MonitoringDashboardTest(APITestCase):
    def setUp(self):
        # Create test data
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='test@lawyer.com',
            hourly_rate=Decimal('400.00')
        )
        
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com'
        )
        
        self.mandate = Mandate.objects.create(
            name='Test Mandate',
            client=self.client_obj,
            due_date=date.today() + timedelta(days=30)
        )
        self.mandate.lawyers.add(self.lawyer)
        
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@lawyer.com',
            password='adminpass123',
            role='admin',
            lawyer_profile=self.lawyer
        )
        
        # Create a separate lawyer for regular user
        self.lawyer2 = Lawyer.objects.create(
            name='Regular Lawyer',  
            email='regular@lawyer.com',
            hourly_rate=Decimal('350.00')
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@lawyer.com',
            password='regularpass123',
            role='lawyer',
            lawyer_profile=self.lawyer2
        )

    def test_dashboard_stats_admin_access(self):
        """Test that admin users can access dashboard stats"""
        url = reverse('monitoring-dashboard')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_requests_today', response.data)
        self.assertIn('failed_requests_today', response.data)
        self.assertIn('unique_users_today', response.data)
        self.assertIn('avg_response_time', response.data)
        self.assertIn('last_updated', response.data)

    def test_dashboard_stats_regular_user_forbidden(self):
        """Test that regular users cannot access dashboard stats"""
        url = reverse('monitoring-dashboard')
        self.client.force_authenticate(user=self.regular_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_stats_unauthenticated_forbidden(self):
        """Test that unauthenticated users cannot access dashboard stats"""
        url = reverse('monitoring-dashboard')
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_dashboard_stats_data_accuracy(self):
        """Test that dashboard stats return accurate data"""
        url = reverse('monitoring-dashboard')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify response contains expected metrics
        self.assertIsInstance(response.data['total_requests_today'], int)
        self.assertIsInstance(response.data['failed_requests_today'], int)
        self.assertIsInstance(response.data['avg_response_time'], (int, float))
        self.assertIn('log_files_sizes', response.data)


class SystemHealthCheckTest(TestCase):
    @patch('monitoring.management.commands.check_system_health.Command.send_alert_email')
    def test_system_health_check_command(self, mock_send_email):
        """Test the system health check management command"""
        # Capture output
        out = StringIO()
        call_command('check_system_health', '--dry-run', stdout=out)
        
        # Check output
        output = out.getvalue()
        self.assertIn('Starting system health check', output)

    def test_system_health_check_no_issues(self):
        """Test system health check when no issues are found"""
        out = StringIO()
        call_command('check_system_health', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Starting system health check', output)


class LoggingIntegrationTest(APITestCase):
    def setUp(self):
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='test@lawyer.com',
            hourly_rate=Decimal('400.00')
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@lawyer.com',
            password='adminpass123',
            role='admin',
            lawyer_profile=self.lawyer
        )

    def test_monitoring_endpoint_logging(self):
        """Test that monitoring endpoints work correctly"""
        url = reverse('monitoring-dashboard')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_requests_today', response.data)

    def test_error_logging_on_monitoring_failure(self):
        """Test that errors in monitoring endpoints are properly logged"""
        url = reverse('monitoring-dashboard')
        # Don't authenticate to trigger 401 error
        
        with patch('legal_backend.middleware.api_logger') as mock_logger:
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
            # Verify error response was logged
            mock_logger.info.assert_called()
            response_logs = [call[0][0] for call in mock_logger.info.call_args_list 
                           if 'type: RESPONSE' in call[0][0]]
            
            self.assertTrue(any('status: 401' in log for log in response_logs))


class MonitoringSecurityTest(APITestCase):
    def setUp(self):
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='test@lawyer.com',
            hourly_rate=Decimal('400.00')
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@lawyer.com',
            password='adminpass123',
            role='admin',
            lawyer_profile=self.lawyer
        )
        
        # Create a separate lawyer for regular user
        self.lawyer2 = Lawyer.objects.create(
            name='Regular Lawyer',  
            email='regular@lawyer.com',
            hourly_rate=Decimal('350.00')
        )
        
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@lawyer.com',
            password='regularpass123',
            role='lawyer',
            lawyer_profile=self.lawyer2
        )

    def test_sensitive_data_not_exposed_in_monitoring(self):
        """Test that monitoring endpoints don't expose sensitive data"""
        url = reverse('monitoring-dashboard')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Convert response to string to check for sensitive data
        response_str = json.dumps(response.data)
        
        # Should not contain any password hashes or tokens
        self.assertNotIn('password', response_str.lower())
        self.assertNotIn('token', response_str.lower())
        self.assertNotIn('pbkdf2', response_str.lower())

    def test_monitoring_access_attempts_logged(self):
        """Test that monitoring access attempts are logged"""
        url = reverse('monitoring-dashboard')
        
        # Test admin access
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test regular user access (should be forbidden)
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MonitoringPerformanceTest(APITestCase):
    def setUp(self):
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='test@lawyer.com',
            hourly_rate=Decimal('400.00')
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@lawyer.com',
            password='adminpass123',
            role='admin',
            lawyer_profile=self.lawyer
        )

    @patch('legal_backend.middleware.performance_logger')
    def test_monitoring_endpoint_performance_logged(self, mock_perf_logger):
        """Test that monitoring endpoint performance is tracked"""
        url = reverse('monitoring-dashboard')
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify performance was logged
        mock_perf_logger.info.assert_called()

    def test_monitoring_endpoints_response_time(self):
        """Test that monitoring endpoints respond within acceptable time"""
        import time
        
        urls = [
            reverse('monitoring-dashboard')
        ]
        
        self.client.force_authenticate(user=self.admin_user)
        
        for url in urls:
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Response should be under 1 second
            response_time = end_time - start_time
            self.assertLess(response_time, 1.0, 
                          f"Endpoint {url} took {response_time:.3f}s to respond")