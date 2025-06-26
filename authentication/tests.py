from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import Lawyer, Client, Mandate, TimeEntry
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='lawyer@test.com',
            hourly_rate=Decimal('400.00')
        )
        
    def test_user_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='lawyer'
        )
        self.assertEqual(user.email, 'test@test.com')
        self.assertEqual(user.role, 'lawyer')
        self.assertTrue(user.is_regular_lawyer)
        self.assertFalse(user.is_admin_lawyer)
        
    def test_admin_user_creation(self):
        user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            role='admin'
        )
        self.assertTrue(user.is_admin_lawyer)
        self.assertFalse(user.is_regular_lawyer)
        
    def test_user_lawyer_profile_link(self):
        user = User.objects.create_user(
            username='lawyer',
            email='lawyer@test.com',
            password='pass123',
            lawyer_profile=self.lawyer
        )
        self.assertEqual(user.lawyer_profile, self.lawyer)
        self.assertEqual(self.lawyer.user_account, user)


class AuthenticationAPITest(APITestCase):
    def setUp(self):
        self.lawyer = Lawyer.objects.create(
            name='Test Lawyer',
            email='lawyer@test.com',
            hourly_rate=Decimal('400.00')
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin',
            first_name='Admin',
            last_name='User'
        )
        
        self.regular_user = User.objects.create_user(
            username='lawyer',
            email='lawyer@test.com',
            password='lawyer123',
            role='lawyer',
            lawyer_profile=self.lawyer,
            first_name='Regular',
            last_name='Lawyer'
        )
        
    def test_login_success(self):
        url = reverse('token_obtain_pair')
        data = {
            'email': 'admin@test.com',
            'password': 'admin123'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['role'], 'admin')
        
    def test_login_invalid_credentials(self):
        url = reverse('token_obtain_pair')
        data = {
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_user_registration_admin_only(self):
        """Test that only admin users can register new users"""
        url = reverse('user_register')
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'lawyer'
        }
        
        # Unauthenticated request should fail
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Regular lawyer should not be able to register users
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin should be able to register users
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_user_profile_access(self):
        """Test user profile access"""
        url = reverse('user_profile')
        
        # Unauthenticated access should fail
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Authenticated user should see their own profile
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'lawyer@test.com')


class PermissionsTest(APITestCase):
    def setUp(self):
        # Create test data
        self.client_obj = Client.objects.create(
            name='Test Client',
            email='client@test.com'
        )
        
        self.lawyer1 = Lawyer.objects.create(
            name='Lawyer One',
            email='lawyer1@test.com',
            hourly_rate=Decimal('400.00')
        )
        
        self.lawyer2 = Lawyer.objects.create(
            name='Lawyer Two',
            email='lawyer2@test.com',
            hourly_rate=Decimal('350.00')
        )
        
        # Create users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin',
            lawyer_profile=self.lawyer1
        )
        
        self.regular_user = User.objects.create_user(
            username='lawyer',
            email='lawyer@test.com',
            password='lawyer123',
            role='lawyer',
            lawyer_profile=self.lawyer2
        )
        
        # Create mandate assigned to lawyer1 only
        self.mandate = Mandate.objects.create(
            name='Test Mandate',
            client=self.client_obj,
            due_date=date.today() + timedelta(days=30)
        )
        self.mandate.lawyers.add(self.lawyer1)
        
        # Create time entry by lawyer1
        self.time_entry = TimeEntry.objects.create(
            mandate=self.mandate,
            lawyer=self.lawyer1,
            date=date.today(),
            hours=Decimal('4.0'),
            description='Test work'
        )
        
    def test_mandate_access_permissions(self):
        """Test mandate access based on role and assignment"""
        url = reverse('mandate-list')
        
        # Unauthenticated access should fail
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Admin can see all mandates
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Regular lawyer can only see assigned mandates
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # Not assigned
        
    def test_time_entry_access_permissions(self):
        """Test time entry access based on role and ownership"""
        url = reverse('timeentry-list')
        
        # Admin can see all time entries
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # Regular lawyer can only see their own time entries
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)  # Not their entry
        
    def test_client_modification_permissions(self):
        """Test that only admins can modify clients"""
        url = reverse('client-list')
        data = {
            'name': 'New Client',
            'email': 'newclient@test.com',
            'phone': '555-0123',
            'address': '123 Test Street'
        }
        
        # Regular lawyer cannot create clients
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin can create clients
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_time_entry_creation_auto_assignment(self):
        """Test that regular lawyers are automatically assigned to their time entries"""
        url = reverse('timeentry-list')
        data = {
            'mandate': self.mandate.id,
            'lawyer': self.lawyer2.id,  # Include lawyer in request
            'date': date.today(),
            'hours': '3.0',
            'description': 'New work entry'
        }
        
        # Add regular user's lawyer to the mandate so they can create entries
        self.mandate.lawyers.add(self.lawyer2)
        
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(url, data)
        
        # Should succeed
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify the entry was created with correct lawyer
        time_entry = TimeEntry.objects.get(id=response.data['id'])
        self.assertEqual(time_entry.lawyer, self.lawyer2)