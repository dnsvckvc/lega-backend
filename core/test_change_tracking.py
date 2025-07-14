"""
Unit tests for change tracking functionality.
"""

import json
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Client, Lawyer, Mandate, TimeEntry, ChangeLog
from .change_tracker import ChangeTracker


User = get_user_model()


class ChangeTrackerTestCase(TestCase):
    """Test cases for the ChangeTracker service."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.regular_user = User.objects.create_user(
            username='lawyer',
            email='lawyer@test.com',
            password='testpass123',
            role='lawyer'
        )
        
        self.client = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            phone='123-456-7890',
            address='123 Test St'
        )
        
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='lawyer@test.com',
            phone='123-456-7890',
            hourly_rate=Decimal('150.00')
        )
        
        self.mandate = Mandate.objects.create(
            name='Test Mandate',
            description='Test mandate description',
            client=self.client,
            due_date=date.today() + timedelta(days=30),
            cost_ceiling=Decimal('5000.00')
        )
        self.mandate.lawyers.add(self.lawyer)
        
        self.time_entry = TimeEntry.objects.create(
            mandate=self.mandate,
            lawyer=self.lawyer,
            date=date.today(),
            hours=Decimal('2.5'),
            description='Test work'
        )
    
    def test_track_model_creation(self):
        """Test tracking model creation."""
        # Clear any existing change logs
        ChangeLog.objects.all().delete()
        
        # Track creation
        ChangeTracker.track_model_creation(self.client, self.admin_user)
        
        # Check that change logs were created
        change_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            object_id=self.client.id,
            change_type='CREATE'
        )
        
        self.assertTrue(change_logs.exists())
        self.assertEqual(change_logs.count(), 4)  # name, email, phone, address
        
        # Check specific field change
        name_change = change_logs.get(field_name='name')
        self.assertEqual(name_change.old_value, 'null')
        self.assertEqual(json.loads(name_change.new_value), 'Test Client')
        self.assertEqual(name_change.changed_by, self.admin_user)
    
    def test_track_model_update(self):
        """Test tracking model updates."""
        # Clear any existing change logs
        ChangeLog.objects.all().delete()
        
        # Create a copy for comparison
        old_client = Client.objects.get(id=self.client.id)
        
        # Modify the client
        self.client.name = 'Updated Client Name'
        self.client.email = 'updated@test.com'
        self.client.save()
        
        # Track the update
        ChangeTracker.track_model_update(self.client, old_client, self.admin_user)
        
        # Check that change logs were created
        change_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            object_id=self.client.id,
            change_type='UPDATE'
        )
        
        self.assertEqual(change_logs.count(), 2)  # name and email changed
        
        # Check name change
        name_change = change_logs.get(field_name='name')
        self.assertEqual(json.loads(name_change.old_value), 'Test Client')
        self.assertEqual(json.loads(name_change.new_value), 'Updated Client Name')
        
        # Check email change
        email_change = change_logs.get(field_name='email')
        self.assertEqual(json.loads(email_change.old_value), 'client@test.com')
        self.assertEqual(json.loads(email_change.new_value), 'updated@test.com')
    
    def test_track_model_deletion(self):
        """Test tracking model deletion."""
        # Clear any existing change logs
        ChangeLog.objects.all().delete()
        
        client_id = self.client.id
        
        # Track deletion
        ChangeTracker.track_model_deletion(self.client, self.admin_user)
        
        # Check that change logs were created
        change_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            object_id=client_id,
            change_type='DELETE'
        )
        
        self.assertTrue(change_logs.exists())
        self.assertEqual(change_logs.count(), 4)  # name, email, phone, address
        
        # Check specific field change
        name_change = change_logs.get(field_name='name')
        self.assertEqual(json.loads(name_change.old_value), 'Test Client')
        self.assertEqual(name_change.new_value, 'null')
    
    def test_excluded_fields_not_tracked(self):
        """Test that excluded fields are not tracked."""
        # Clear any existing change logs
        ChangeLog.objects.all().delete()
        
        # Track creation (should not track created_at, updated_at, id)
        ChangeTracker.track_model_creation(self.client, self.admin_user)
        
        # Check that excluded fields are not tracked
        change_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            object_id=self.client.id
        )
        
        excluded_fields = ['created_at', 'updated_at', 'id']
        for field in excluded_fields:
            self.assertFalse(
                change_logs.filter(field_name=field).exists(),
                f"Field '{field}' should not be tracked"
            )
    
    def test_serialize_value_json(self):
        """Test value serialization to JSON."""
        # Test various data types
        test_cases = [
            ('string', '"string"'),
            (123, '123'),
            (123.45, '123.45'),
            (True, 'true'),
            (False, 'false'),
            (None, 'null'),
            ([1, 2, 3], '[1, 2, 3]'),
            ({'key': 'value'}, '{"key": "value"}'),
            (date(2025, 7, 14), '"2025-07-14"'),
        ]
        
        for value, expected in test_cases:
            result = ChangeTracker._serialize_value(value)
            self.assertEqual(result, expected, f"Failed for value: {value}")
    
    def test_serialize_value_fallback(self):
        """Test value serialization fallback for non-JSON serializable objects."""
        # Create a non-JSON serializable object
        class NonSerializable:
            def __str__(self):
                return "non-serializable"
        
        obj = NonSerializable()
        result = ChangeTracker._serialize_value(obj)
        self.assertEqual(result, "non-serializable")


class ChangeTrackingAPITestCase(APITestCase):
    """Test cases for change tracking API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.regular_user = User.objects.create_user(
            username='lawyer',
            email='lawyer@test.com',
            password='testpass123',
            role='lawyer'
        )
        
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='lawyer@test.com',
            phone='123-456-7890',
            hourly_rate=Decimal('150.00')
        )
        
        # Link regular user to lawyer profile
        self.regular_user.lawyer_profile = self.lawyer
        self.regular_user.save()
        
        self.client_model = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            phone='123-456-7890',
            address='123 Test St'
        )
        
        self.mandate = Mandate.objects.create(
            name='Test Mandate',
            description='Test mandate description',
            client=self.client_model,
            due_date=date.today() + timedelta(days=30),
            cost_ceiling=Decimal('5000.00')
        )
        self.mandate.lawyers.add(self.lawyer)
        
        self.time_entry = TimeEntry.objects.create(
            mandate=self.mandate,
            lawyer=self.lawyer,
            date=date.today(),
            hours=Decimal('2.5'),
            description='Test work'
        )
        
        # Create some change logs
        self.create_test_change_logs()
    
    def create_test_change_logs(self):
        """Create test change logs."""
        client_ct = ContentType.objects.get_for_model(Client)
        mandate_ct = ContentType.objects.get_for_model(Mandate)
        
        # Client change log
        ChangeLog.objects.create(
            content_type=client_ct,
            object_id=self.client_model.id,
            field_name='name',
            old_value=json.dumps('Old Client'),
            new_value=json.dumps('Test Client'),
            change_type='UPDATE',
            changed_by=self.admin_user
        )
        
        # Mandate change log
        ChangeLog.objects.create(
            content_type=mandate_ct,
            object_id=self.mandate.id,
            field_name='name',
            old_value=json.dumps('Old Mandate'),
            new_value=json.dumps('Test Mandate'),
            change_type='UPDATE',
            changed_by=self.admin_user
        )
    
    def get_admin_token(self):
        """Get JWT token for admin user."""
        refresh = RefreshToken.for_user(self.admin_user)
        return str(refresh.access_token)
    
    def get_regular_token(self):
        """Get JWT token for regular user."""
        refresh = RefreshToken.for_user(self.regular_user)
        return str(refresh.access_token)
    
    def test_get_change_logs_admin(self):
        """Test getting change logs as admin user."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_get_change_logs_regular_user(self):
        """Test getting change logs as regular user (filtered)."""
        token = self.get_regular_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # Regular users can see client changes and their own mandate/time entry changes
    
    def test_get_change_log_detail(self):
        """Test getting a specific change log."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        change_log = ChangeLog.objects.first()
        url = reverse('changelog-detail', kwargs={'pk': change_log.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], change_log.id)
        self.assertIn('old_value_parsed', response.data)
        self.assertIn('new_value_parsed', response.data)
    
    def test_get_client_changes(self):
        """Test getting client changes only."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-client-changes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # All results should be client changes
        for result in response.data['results']:
            self.assertEqual(result['model_name'], 'client')
    
    def test_get_mandate_changes(self):
        """Test getting mandate changes only."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-mandate-changes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # All results should be mandate changes
        for result in response.data['results']:
            self.assertEqual(result['model_name'], 'mandate')
    
    def test_get_timeentry_changes(self):
        """Test getting time entry changes only."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-timeentry-changes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_get_recent_changes(self):
        """Test getting recent changes (last 24 hours)."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-recent')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_get_user_activity(self):
        """Test getting changes by specific user."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-user-activity')
        response = self.client.get(url, {'user_id': self.admin_user.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # All results should be changes by the admin user
        for result in response.data['results']:
            self.assertEqual(result['changed_by_email'], self.admin_user.email)
    
    def test_get_user_activity_missing_user_id(self):
        """Test getting user activity without user_id parameter."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-user-activity')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_id parameter is required', response.data['error'])
    
    def test_get_object_history(self):
        """Test getting change history for a specific object."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-object-history')
        response = self.client.get(url, {
            'model_name': 'client',
            'object_id': self.client_model.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # All results should be for the specific client
        for result in response.data['results']:
            self.assertEqual(result['model_name'], 'client')
            self.assertEqual(result['object_id'], self.client_model.id)
    
    def test_get_object_history_invalid_model(self):
        """Test getting object history with invalid model name."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-object-history')
        response = self.client.get(url, {
            'model_name': 'invalid_model',
            'object_id': 1
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid model_name', response.data['error'])
    
    def test_filter_changes_by_date_range(self):
        """Test filtering changes by date range."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-list')
        response = self.client.get(url, {
            'changed_at_from': '2025-07-01',
            'changed_at_to': '2025-07-31'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_filter_changes_by_change_type(self):
        """Test filtering changes by change type."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-list')
        response = self.client.get(url, {'change_type': 'UPDATE'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        
        # All results should be UPDATE changes
        for result in response.data['results']:
            self.assertEqual(result['change_type'], 'UPDATE')
    
    def test_search_changes(self):
        """Test searching changes."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('changelog-list')
        response = self.client.get(url, {'search': 'name'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_unauthorized_access(self):
        """Test that unauthorized access is denied."""
        url = reverse('changelog-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangeTrackingIntegrationTestCase(APITestCase):
    """Integration tests for change tracking with CRUD operations."""
    
    def setUp(self):
        """Set up test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='lawyer@test.com',
            phone='123-456-7890',
            hourly_rate=Decimal('150.00')
        )
    
    def get_admin_token(self):
        """Get JWT token for admin user."""
        refresh = RefreshToken.for_user(self.admin_user)
        return str(refresh.access_token)
    
    def test_client_crud_change_tracking(self):
        """Test that client CRUD operations generate change logs."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Clear existing change logs
        ChangeLog.objects.all().delete()
        
        # CREATE - Create a client
        create_url = reverse('client-list')
        client_data = {
            'name': 'Test Client',
            'email': 'client@test.com',
            'phone': '123-456-7890',
            'address': '123 Test St'
        }
        
        response = self.client.post(create_url, client_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        client_id = response.data['id']
        
        # Check that CREATE change logs were generated
        create_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            object_id=client_id,
            change_type='CREATE'
        )
        self.assertTrue(create_logs.exists())
        
        # UPDATE - Update the client
        update_url = reverse('client-detail', kwargs={'pk': client_id})
        updated_data = {
            'name': 'Updated Client',
            'email': 'updated@test.com',
            'phone': '123-456-7890',
            'address': '123 Test St'
        }
        
        response = self.client.put(update_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that UPDATE change logs were generated
        update_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            object_id=client_id,
            change_type='UPDATE'
        )
        self.assertTrue(update_logs.exists())
        
        # Should have changes for name and email
        name_change = update_logs.filter(field_name='name').first()
        self.assertIsNotNone(name_change)
        self.assertEqual(json.loads(name_change.old_value), 'Test Client')
        self.assertEqual(json.loads(name_change.new_value), 'Updated Client')
        
        # DELETE - Delete the client
        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that DELETE change logs were generated
        delete_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Client),
            object_id=client_id,
            change_type='DELETE'
        )
        self.assertTrue(delete_logs.exists())
    
    def test_mandate_crud_change_tracking(self):
        """Test that mandate CRUD operations generate change logs."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Create a client first
        client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            phone='123-456-7890',
            address='123 Test St'
        )
        
        # Clear existing change logs
        ChangeLog.objects.all().delete()
        
        # CREATE - Create a mandate
        create_url = reverse('mandate-list')
        mandate_data = {
            'name': 'Test Mandate',
            'description': 'Test mandate description',
            'client': client_obj.id,
            'lawyers': [self.lawyer.id],
            'due_date': '2025-08-14',
            'cost_ceiling': '5000.00'
        }
        
        response = self.client.post(create_url, mandate_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        mandate_id = response.data['id']
        
        # Check that CREATE change logs were generated
        create_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Mandate),
            object_id=mandate_id,
            change_type='CREATE'
        )
        self.assertTrue(create_logs.exists())
        
        # UPDATE - Update the mandate
        update_url = reverse('mandate-detail', kwargs={'pk': mandate_id})
        updated_data = {
            'name': 'Updated Mandate',
            'description': 'Updated description',
            'client': client_obj.id,
            'lawyers': [self.lawyer.id],
            'due_date': '2025-08-14',
            'cost_ceiling': '6000.00'
        }
        
        response = self.client.put(update_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that UPDATE change logs were generated
        update_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(Mandate),
            object_id=mandate_id,
            change_type='UPDATE'
        )
        self.assertTrue(update_logs.exists())
    
    def test_time_entry_crud_change_tracking(self):
        """Test that time entry CRUD operations generate change logs."""
        token = self.get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Create dependencies
        client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com',
            phone='123-456-7890',
            address='123 Test St'
        )
        
        mandate_obj = Mandate.objects.create(
            name='Test Mandate',
            description='Test mandate description',
            client=client_obj,
            due_date=date.today() + timedelta(days=30),
            cost_ceiling=Decimal('5000.00')
        )
        mandate_obj.lawyers.add(self.lawyer)
        
        # Clear existing change logs
        ChangeLog.objects.all().delete()
        
        # CREATE - Create a time entry
        create_url = reverse('timeentry-list')
        time_entry_data = {
            'mandate': mandate_obj.id,
            'lawyer': self.lawyer.id,
            'date': '2025-07-14',
            'hours': '2.5',
            'description': 'Test work'
        }
        
        response = self.client.post(create_url, time_entry_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        time_entry_id = response.data['id']
        
        # Check that CREATE change logs were generated
        create_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(TimeEntry),
            object_id=time_entry_id,
            change_type='CREATE'
        )
        self.assertTrue(create_logs.exists())
        
        # UPDATE - Update the time entry
        update_url = reverse('timeentry-detail', kwargs={'pk': time_entry_id})
        updated_data = {
            'mandate': mandate_obj.id,
            'lawyer': self.lawyer.id,
            'date': '2025-07-14',
            'hours': '3.0',
            'description': 'Updated work description'
        }
        
        response = self.client.put(update_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that UPDATE change logs were generated
        update_logs = ChangeLog.objects.filter(
            content_type=ContentType.objects.get_for_model(TimeEntry),
            object_id=time_entry_id,
            change_type='UPDATE'
        )
        self.assertTrue(update_logs.exists())
        
        # Should have changes for hours and description
        hours_change = update_logs.filter(field_name='hours').first()
        self.assertIsNotNone(hours_change)
        self.assertEqual(json.loads(hours_change.old_value), '2.50')
        self.assertEqual(json.loads(hours_change.new_value), '3.00')