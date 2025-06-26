from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from .models import Client, Lawyer, Mandate, TimeEntry
from .test_factories import TestDataFactory

User = get_user_model()


class ClientModelTest(TestCase):
    def test_client_creation(self):
        client = TestDataFactory.create_client('Test Corporation', 'contact@testcorp.com')
        self.assertEqual(client.name, 'Test Corporation')
        self.assertEqual(client.email, 'contact@testcorp.com')
        self.assertEqual(str(client), 'Test Corporation')

    def test_client_str_representation(self):
        client = TestDataFactory.create_client('Test Corporation')
        self.assertEqual(str(client), 'Test Corporation')

    def test_client_ordering(self):
        client_a = TestDataFactory.create_client('A Company', 'a@test.com')
        client_z = TestDataFactory.create_client('Z Company', 'z@test.com')
        
        clients = list(Client.objects.all())
        self.assertEqual(clients[0], client_a)
        self.assertEqual(clients[1], client_z)


class LawyerModelTest(TestCase):
    def test_lawyer_creation(self):
        lawyer = TestDataFactory.create_lawyer('John Lawyer', 'john@lawfirm.com', Decimal('350.00'))
        self.assertEqual(lawyer.name, 'John Lawyer')
        self.assertEqual(lawyer.hourly_rate, Decimal('350.00'))
        self.assertEqual(str(lawyer), 'John Lawyer')

    def test_lawyer_hourly_rate_validation(self):
        lawyer = Lawyer(
            name='Test Lawyer',
            email='test@law.com',
            phone='555-0001',
            hourly_rate=Decimal('0.00')
        )
        with self.assertRaises(ValidationError):
            lawyer.full_clean()

    def test_lawyer_str_representation(self):
        lawyer = TestDataFactory.create_lawyer('John Lawyer')
        self.assertEqual(str(lawyer), 'John Lawyer')


class MandateModelTest(TestCase):
    def setUp(self):
        self.client = TestDataFactory.create_client('Test Client', 'client@test.com')
        self.lawyer = TestDataFactory.create_lawyer('Test Lawyer', 'lawyer@test.com', Decimal('400.00'))

    def test_mandate_creation(self):
        mandate = TestDataFactory.create_mandate(
            client=self.client,
            name='Test Mandate',
            due_date=date.today() + timedelta(days=30),
            is_active=True
        )
        self.assertEqual(mandate.name, 'Test Mandate')
        self.assertEqual(mandate.client, self.client)
        self.assertTrue(mandate.is_active)
        self.assertEqual(str(mandate), 'Test Mandate - Test Client')

    def test_mandate_default_is_active(self):
        mandate = TestDataFactory.create_mandate(client=self.client, name='Test Mandate')
        self.assertTrue(mandate.is_active)

    def test_mandate_total_hours_property(self):
        mandate = TestDataFactory.create_mandate(client=self.client, name='Test Mandate')
        mandate.lawyers.add(self.lawyer)
        
        # Add time entries using factory
        time_entry1 = TestDataFactory.create_time_entry(
            mandate=mandate,
            lawyer=self.lawyer,
            hours=Decimal('3.5'),
            entry_date=date.today()
        )
        time_entry2 = TestDataFactory.create_time_entry(
            mandate=mandate,
            lawyer=self.lawyer,
            hours=Decimal('2.0'),
            entry_date=date.today() - timedelta(days=1)
        )
        
        self.assertEqual(mandate.total_hours, Decimal('5.5'))

    def test_mandate_total_cost_property(self):
        mandate = TestDataFactory.create_mandate(client=self.client, name='Test Mandate')
        mandate.lawyers.add(self.lawyer)
        
        time_entry = TestDataFactory.create_time_entry(
            mandate=mandate,
            lawyer=self.lawyer,
            hours=Decimal('3.5'),
            entry_date=date.today()
        )
        
        expected_cost = Decimal('3.5') * self.lawyer.hourly_rate
        self.assertEqual(mandate.total_cost, expected_cost)

    def test_mandate_str_representation(self):
        mandate = TestDataFactory.create_mandate(client=self.client, name='Test Mandate')
        self.assertEqual(str(mandate), 'Test Mandate - Test Client')


class TimeEntryModelTest(TestCase):
    def setUp(self):
        self.client = TestDataFactory.create_client('Test Client', 'client@test.com')
        self.lawyer = TestDataFactory.create_lawyer('Test Lawyer', 'lawyer@test.com', Decimal('400.00'))
        self.mandate = TestDataFactory.create_mandate(
            client=self.client,
            name='Test Mandate',
            due_date=date.today() + timedelta(days=30)
        )
        self.mandate.lawyers.add(self.lawyer)

    def test_time_entry_creation(self):
        time_entry = TestDataFactory.create_time_entry(
            mandate=self.mandate,
            lawyer=self.lawyer,
            hours=Decimal('4.5'),
            entry_date=date.today(),
            description='Legal research'
        )
        
        self.assertEqual(time_entry.mandate, self.mandate)
        self.assertEqual(time_entry.lawyer, self.lawyer)
        self.assertEqual(time_entry.hours, Decimal('4.5'))

    def test_time_entry_cost_property(self):
        time_entry = TestDataFactory.create_time_entry(
            mandate=self.mandate,
            lawyer=self.lawyer,
            hours=Decimal('4.5'),
            entry_date=date.today(),
            description='Legal research'
        )
        
        expected_cost = Decimal('4.5') * Decimal('400.00')
        self.assertEqual(time_entry.cost, expected_cost)

    def test_time_entry_hours_validation(self):
        time_entry = TimeEntry(
            mandate=self.mandate,
            lawyer=self.lawyer,
            date=date.today(),
            hours=Decimal('0.00'),
            description='Invalid hours'
        )
        
        with self.assertRaises(ValidationError):
            time_entry.full_clean()

    def test_time_entry_str_representation(self):
        time_entry = TestDataFactory.create_time_entry(
            mandate=self.mandate,
            lawyer=self.lawyer,
            hours=Decimal('4.5'),
            entry_date=date.today(),
            description='Legal research'
        )
        
        expected_str = f"Test Lawyer - Test Mandate - 4.5h on {date.today()}"
        self.assertEqual(str(time_entry), expected_str)
