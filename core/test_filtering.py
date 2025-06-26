from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from .models import Client, Lawyer, Mandate, TimeEntry
from .test_factories import TestDataFactory

User = get_user_model()


class MandateFilteringTest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
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
        
        # Create mandates with different statuses
        self.active_future_mandate = TestDataFactory.create_mandate(
            name='Active Future Mandate',
            description='Active mandate due in future',
            client=self.test_client,
            due_date=date.today() + timedelta(days=30),
            is_active=True
        )
        
        self.active_overdue_mandate = TestDataFactory.create_mandate(
            name='Active Overdue Mandate',
            description='Active mandate past due date',
            client=self.test_client,
            due_date=date.today() - timedelta(days=10),
            is_active=True
        )
        
        self.inactive_future_mandate = TestDataFactory.create_mandate(
            name='Inactive Future Mandate',
            description='Inactive mandate with future due date',
            client=self.test_client,
            due_date=date.today() + timedelta(days=15),
            is_active=False
        )
        
        self.inactive_overdue_mandate = TestDataFactory.create_mandate(
            name='Inactive Overdue Mandate',
            description='Inactive mandate past due date',
            client=self.test_client,
            due_date=date.today() - timedelta(days=5),
            is_active=False
        )

    def test_filter_active_mandates(self):
        url = reverse('mandate-list')
        response = self.client.get(url, {'status': 'active'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        mandate_names = [mandate['name'] for mandate in response.data['results']]
        self.assertIn('Active Future Mandate', mandate_names)
        self.assertIn('Active Overdue Mandate', mandate_names)
        self.assertNotIn('Inactive Future Mandate', mandate_names)
        self.assertNotIn('Inactive Overdue Mandate', mandate_names)

    def test_filter_inactive_mandates(self):
        url = reverse('mandate-list')
        response = self.client.get(url, {'status': 'inactive'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        mandate_names = [mandate['name'] for mandate in response.data['results']]
        self.assertIn('Inactive Future Mandate', mandate_names)
        self.assertIn('Inactive Overdue Mandate', mandate_names)
        self.assertNotIn('Active Future Mandate', mandate_names)
        self.assertNotIn('Active Overdue Mandate', mandate_names)

    def test_filter_overdue_mandates(self):
        """Test that overdue filter returns only active AND overdue mandates"""
        url = reverse('mandate-list')
        response = self.client.get(url, {'status': 'overdue'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        mandate = response.data['results'][0]
        self.assertEqual(mandate['name'], 'Active Overdue Mandate')
        self.assertTrue(mandate['is_active'])
        # Verify due date is in the past
        mandate_due_date = date.fromisoformat(mandate['due_date'])
        self.assertLess(mandate_due_date, date.today())

    def test_filter_by_is_active_parameter(self):
        url = reverse('mandate-list')
        
        # Test is_active=true
        response = self.client.get(url, {'is_active': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Test is_active=false
        response = self.client.get(url, {'is_active': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Test is_active=1 (alternative true format)
        response = self.client.get(url, {'is_active': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_by_due_date_range(self):
        url = reverse('mandate-list')
        
        # Test filtering by due_date_from
        future_date = date.today() + timedelta(days=20)
        response = self.client.get(url, {'due_date_from': future_date})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active Future Mandate')
        
        # Test filtering by due_date_to
        past_date = date.today() - timedelta(days=1)
        response = self.client.get(url, {'due_date_to': past_date})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_search_mandates(self):
        url = reverse('mandate-list')
        
        # Search by mandate name (more specific search)
        response = self.client.get(url, {'search': 'Future'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Future and Inactive Future
        
        # Search for a unique term
        response = self.client.get(url, {'search': 'Overdue'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Active Overdue and Inactive Overdue
        
        # Search by client name
        response = self.client.get(url, {'search': 'Test Client'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)

    def test_combined_filters(self):
        """Test combining multiple filters"""
        url = reverse('mandate-list')
        
        # Combine status=active and due_date filtering
        future_date = date.today() + timedelta(days=20)
        response = self.client.get(url, {
            'status': 'active',
            'due_date_from': future_date
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Active Future Mandate')

    def test_ordering(self):
        url = reverse('mandate-list')
        
        # Test ordering by name
        response = self.client.get(url, {'ordering': 'name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mandate_names = [mandate['name'] for mandate in response.data['results']]
        self.assertEqual(mandate_names[0], 'Active Future Mandate')
        
        # Test ordering by due_date descending
        response = self.client.get(url, {'ordering': '-due_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mandate_names = [mandate['name'] for mandate in response.data['results']]
        self.assertEqual(mandate_names[0], 'Active Future Mandate')  # Furthest in future


class TimeEntryFilteringTest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin2',
            email='admin2@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.test_client = TestDataFactory.create_client(
            name='Test Client', email='client@test.com'
        )
        self.test_lawyer1 = TestDataFactory.create_lawyer(
            name='Lawyer One', email='lawyer1@test.com',
            hourly_rate=Decimal('400.00')
        )
        self.test_lawyer2 = TestDataFactory.create_lawyer(
            name='Lawyer Two', email='lawyer2@test.com',
            hourly_rate=Decimal('350.00')
        )
        self.test_mandate = TestDataFactory.create_mandate(
            name='Test Mandate',
            client=self.test_client,
            due_date=date.today() + timedelta(days=30)
        )
        self.test_mandate.lawyers.add(self.test_lawyer1, self.test_lawyer2)
        
        # Create time entries with different dates
        self.today_entry = TestDataFactory.create_time_entry(
            mandate=self.test_mandate, lawyer=self.test_lawyer1,
            entry_date=date.today(), hours=Decimal('4.0'),
            description='Today work'
        )
        self.week_ago_entry = TestDataFactory.create_time_entry(
            mandate=self.test_mandate, lawyer=self.test_lawyer2,
            entry_date=date.today() - timedelta(days=7), hours=Decimal('6.0'),
            description='Week ago work'
        )
        self.month_ago_entry = TestDataFactory.create_time_entry(
            mandate=self.test_mandate, lawyer=self.test_lawyer1,
            entry_date=date.today() - timedelta(days=30), hours=Decimal('3.0'),
            description='Month ago work'
        )

    def test_filter_time_entries_by_date_range(self):
        url = reverse('timeentry-list')
        
        # Filter for entries in the last week
        week_ago = date.today() - timedelta(days=7)
        response = self.client.get(url, {'date_from': week_ago})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Filter for entries up to a week ago
        response = self.client.get(url, {'date_to': week_ago})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_time_entries_by_lawyer(self):
        url = reverse('timeentry-list')
        response = self.client.get(url, {'lawyer': self.test_lawyer1.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        for entry in response.data['results']:
            self.assertEqual(entry['lawyer_name'], 'Lawyer One')

    def test_filter_time_entries_by_mandate(self):
        # Create another mandate and time entry
        other_mandate = TestDataFactory.create_mandate(
            name='Other Mandate',
            client=self.test_client,
            due_date=date.today() + timedelta(days=45)
        )
        other_mandate.lawyers.add(self.test_lawyer1)
        
        other_entry = TestDataFactory.create_time_entry(
            mandate=other_mandate, lawyer=self.test_lawyer1,
            entry_date=date.today(), hours=Decimal('2.0'),
            description='Other mandate work'
        )
        
        url = reverse('timeentry-list')
        response = self.client.get(url, {'mandate': self.test_mandate.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_search_time_entries(self):
        url = reverse('timeentry-list')
        
        # Search by description
        response = self.client.get(url, {'search': 'Today'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['description'], 'Today work')

    def test_order_time_entries(self):
        url = reverse('timeentry-list')
        
        # Order by hours ascending
        response = self.client.get(url, {'ordering': 'hours'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hours_list = [float(entry['hours']) for entry in response.data['results']]
        self.assertEqual(hours_list, sorted(hours_list))


class LawyerFilteringTest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin3',
            email='admin3@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.lawyer1 = TestDataFactory.create_lawyer(
            name='Alice Attorney', email='alice@law.com',
            hourly_rate=Decimal('450.00')
        )
        self.lawyer2 = TestDataFactory.create_lawyer(
            name='Bob Barrister', email='bob@law.com',
            hourly_rate=Decimal('350.00')
        )

    def test_search_lawyers(self):
        url = reverse('lawyer-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'Alice'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Alice Attorney')
        
        # Search by email
        response = self.client.get(url, {'search': 'bob@law.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Bob Barrister')

    def test_order_lawyers(self):
        url = reverse('lawyer-list')
        
        # Order by hourly rate
        response = self.client.get(url, {'ordering': 'hourly_rate'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rates = [float(lawyer['hourly_rate']) for lawyer in response.data['results']]
        self.assertEqual(rates, sorted(rates))


class ClientFilteringTest(APITestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin4',
            email='admin4@test.com',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.client1 = TestDataFactory.create_client(
            name='Apple Corp', email='contact@apple.com'
        )
        self.client2 = TestDataFactory.create_client(
            name='Banana Inc', email='info@banana.com'
        )

    def test_search_clients(self):
        url = reverse('client-list')
        
        # Search by name
        response = self.client.get(url, {'search': 'Apple'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Apple Corp')
        
        # Search by email
        response = self.client.get(url, {'search': 'banana.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Banana Inc')