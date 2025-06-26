from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from .models import Client, Lawyer, Mandate, TimeEntry
from .test_factories import TestDataFactory

User = get_user_model()


class ClientAPITest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.client_data = {
            'name': 'Test Corporation',
            'email': 'contact@testcorp.com',
            'phone': '555-0123',
            'address': '123 Test Street, Test City, TC 12345'
        }
        self.test_client = TestDataFactory.create_client(**self.client_data)

    def test_get_clients_list(self):
        url = reverse('client-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Corporation')

    def test_create_client(self):
        url = reverse('client-list')
        new_client_data = {
            'name': 'New Corporation',
            'email': 'new@corp.com',
            'phone': '555-0124',
            'address': '456 New Street'
        }
        
        response = self.client.post(url, new_client_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Corporation')

    def test_get_client_detail(self):
        url = reverse('client-detail', kwargs={'pk': self.test_client.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Corporation')

    def test_update_client(self):
        url = reverse('client-detail', kwargs={'pk': self.test_client.pk})
        updated_data = {'name': 'Updated Corporation'}
        
        response = self.client.patch(url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Corporation')

    def test_delete_client(self):
        url = reverse('client-detail', kwargs={'pk': self.test_client.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Client.objects.count(), 0)

    def test_client_mandates_endpoint(self):
        # Create a mandate for the client
        lawyer = TestDataFactory.create_lawyer(
            name='Test Lawyer', email='lawyer@test.com',
            hourly_rate=Decimal('400.00')
        )
        mandate = TestDataFactory.create_mandate(
            name='Test Mandate',
            client=self.test_client,
            due_date=date.today() + timedelta(days=30)
        )
        
        url = reverse('client-mandates', kwargs={'pk': self.test_client.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Mandate')


class LawyerAPITest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin2',
            email='admin2@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.lawyer_data = {
            'name': 'John Lawyer',
            'email': 'john@lawfirm.com',
            'phone': '555-0456',
            'hourly_rate': '350.00'
        }
        self.test_lawyer = TestDataFactory.create_lawyer(
            name='John Lawyer',
            email='john@lawfirm.com',
            hourly_rate=Decimal('350.00')
        )

    def test_get_lawyers_list(self):
        url = reverse('lawyer-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'John Lawyer')

    def test_create_lawyer(self):
        url = reverse('lawyer-list')
        new_lawyer_data = {
            'name': 'Jane Lawyer',
            'email': 'jane@lawfirm.com',
            'phone': '555-0457',
            'hourly_rate': '380.00'
        }
        
        response = self.client.post(url, new_lawyer_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Jane Lawyer')

    def test_lawyer_monthly_billing(self):
        # Create test data
        test_client = TestDataFactory.create_client(
            name='Test Client', email='client@test.com'
        )
        mandate = TestDataFactory.create_mandate(
            name='Test Mandate',
            client=test_client,
            due_date=date.today() + timedelta(days=30)
        )
        mandate.lawyers.add(self.test_lawyer)
        
        time_entry = TestDataFactory.create_time_entry(
            mandate=mandate, lawyer=self.test_lawyer,
            entry_date=date.today(), hours=Decimal('5.0'),
            description='Test work'
        )
        
        url = reverse('lawyer-monthly-billing', kwargs={'pk': self.test_lawyer.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['lawyer_name'], 'John Lawyer')
        self.assertEqual(response.data['total_hours'], Decimal('5.0'))
        self.assertEqual(response.data['total_amount'], Decimal('1750.0'))


class MandateAPITest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin3',
            email='admin3@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.test_client = TestDataFactory.create_client(
            name='Test Client', email='client@test.com'
        )
        self.test_lawyer = TestDataFactory.create_lawyer(
            name='Test Lawyer', email='lawyer@test.com',
            hourly_rate=Decimal('400.00')
        )
        
        # Active mandate
        self.active_mandate = TestDataFactory.create_mandate(
            name='Active Mandate',
            client=self.test_client,
            due_date=date.today() + timedelta(days=30),
            is_active=True
        )
        self.active_mandate.lawyers.add(self.test_lawyer)
        
        # Inactive mandate
        self.inactive_mandate = TestDataFactory.create_mandate(
            name='Inactive Mandate',
            client=self.test_client,
            due_date=date.today() - timedelta(days=30),
            is_active=False
        )
        
        # Overdue but active mandate
        self.overdue_mandate = TestDataFactory.create_mandate(
            name='Overdue Mandate',
            client=self.test_client,
            due_date=date.today() - timedelta(days=10),
            is_active=True
        )
        self.overdue_mandate.lawyers.add(self.test_lawyer)

    def test_get_mandates_list(self):
        url = reverse('mandate-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_create_mandate(self):
        url = reverse('mandate-list')
        mandate_data = {
            'name': 'New Mandate',
            'description': 'New test mandate',
            'client': self.test_client.id,
            'lawyers': [self.test_lawyer.id],
            'due_date': date.today() + timedelta(days=45),
            'cost_ceiling': '75000.00',
            'is_active': True
        }
        
        response = self.client.post(url, mandate_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Mandate')

    def test_mandate_summary(self):
        # Add time entry
        time_entry = TestDataFactory.create_time_entry(
            mandate=self.active_mandate, lawyer=self.test_lawyer,
            entry_date=date.today(), hours=Decimal('8.0'),
            description='Development work'
        )
        
        url = reverse('mandate-summary', kwargs={'pk': self.active_mandate.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mandate_name'], 'Active Mandate')
        self.assertEqual(response.data['total_hours'], Decimal('8.0'))
        self.assertEqual(response.data['total_cost'], Decimal('3200.0'))


class TimeEntryAPITest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin4',
            email='admin4@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.test_client = TestDataFactory.create_client(
            name='Test Client', email='client@test.com'
        )
        self.test_lawyer = TestDataFactory.create_lawyer(
            name='Test Lawyer', email='lawyer@test.com',
            hourly_rate=Decimal('400.00')
        )
        self.test_mandate = TestDataFactory.create_mandate(
            name='Test Mandate',
            client=self.test_client,
            due_date=date.today() + timedelta(days=30)
        )
        self.test_mandate.lawyers.add(self.test_lawyer)
        
        self.time_entry = TestDataFactory.create_time_entry(
            mandate=self.test_mandate, lawyer=self.test_lawyer,
            entry_date=date.today(), hours=Decimal('6.0'),
            description='Legal research'
        )

    def test_get_time_entries_list(self):
        url = reverse('timeentry-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['hours'], '6.00')

    def test_create_time_entry(self):
        url = reverse('timeentry-list')
        time_entry_data = {
            'mandate': self.test_mandate.id,
            'lawyer': self.test_lawyer.id,
            'date': date.today(),
            'hours': '4.5',
            'description': 'Contract review'
        }
        
        response = self.client.post(url, time_entry_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['hours'], '4.50')

    def test_time_entry_date_filtering(self):
        # Create additional time entries
        past_entry = TestDataFactory.create_time_entry(
            mandate=self.test_mandate, lawyer=self.test_lawyer,
            entry_date=date.today() - timedelta(days=5), hours=Decimal('3.0'),
            description='Past work'
        )
        old_entry = TestDataFactory.create_time_entry(
            mandate=self.test_mandate, lawyer=self.test_lawyer,
            entry_date=date.today() - timedelta(days=35), hours=Decimal('2.0'),
            description='Old work'
        )
        
        url = reverse('timeentry-list')
        # Filter for entries in the last week
        week_ago = date.today() - timedelta(days=7)
        response = self.client.get(url, {'date_from': week_ago})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Today and 5 days ago

    def test_time_entry_invalid_lawyer_mandate_combination(self):
        # Create another lawyer not assigned to the mandate
        other_lawyer = TestDataFactory.create_lawyer(
            name='Other Lawyer', email='other@test.com',
            hourly_rate=Decimal('350.00')
        )
        
        url = reverse('timeentry-list')
        invalid_data = {
            'mandate': self.test_mandate.id,
            'lawyer': other_lawyer.id,
            'date': date.today(),
            'hours': '2.0',
            'description': 'Invalid entry'
        }
        
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)