from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from .models import Client, Lawyer, Mandate, TimeEntry
from .serializers import (
    ClientSerializer, LawyerSerializer, MandateSerializer,
    MandateDetailSerializer, TimeEntrySerializer
)
from .test_factories import TestDataFactory

User = get_user_model()


class ClientSerializerTest(TestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.client_data = {
            'name': 'Test Corporation',
            'email': 'contact@testcorp.com',
            'phone': '555-0123',
            'address': '123 Test Street, Test City, TC 12345'
        }
        self.client = TestDataFactory.create_client(**self.client_data)

    def test_client_serialization(self):
        serializer = ClientSerializer(instance=self.client)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Corporation')
        self.assertEqual(data['email'], 'contact@testcorp.com')
        self.assertEqual(data['mandates_count'], 0)

    def test_client_deserialization(self):
        serializer = ClientSerializer(data=self.client_data)
        self.assertTrue(serializer.is_valid())
        
        client = serializer.save()
        self.assertEqual(client.name, 'Test Corporation')
        self.assertEqual(client.email, 'contact@testcorp.com')

    def test_client_mandates_count(self):
        # Create a mandate for the client using factory
        TestDataFactory.create_mandate(
            client=self.client,
            name='Test Mandate',
            due_date=date.today() + timedelta(days=30)
        )
        
        serializer = ClientSerializer(instance=self.client)
        self.assertEqual(serializer.data['mandates_count'], 1)


class LawyerSerializerTest(TestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin2',
            email='admin2@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.lawyer_data = {
            'name': 'John Lawyer',
            'email': 'john@lawfirm.com',
            'phone': '555-0456',
            'hourly_rate': '350.00'
        }
        self.lawyer = TestDataFactory.create_lawyer(
            name='John Lawyer',
            email='john@lawfirm.com',
            hourly_rate=Decimal('350.00')
        )

    def test_lawyer_serialization(self):
        serializer = LawyerSerializer(instance=self.lawyer)
        data = serializer.data
        
        self.assertEqual(data['name'], 'John Lawyer')
        self.assertEqual(data['hourly_rate'], '350.00')
        self.assertEqual(data['mandates_count'], 0)

    def test_lawyer_deserialization(self):
        serializer = LawyerSerializer(data=self.lawyer_data)
        self.assertTrue(serializer.is_valid())
        
        lawyer = serializer.save()
        self.assertEqual(lawyer.name, 'John Lawyer')
        self.assertEqual(lawyer.hourly_rate, Decimal('350.00'))

    def test_lawyer_invalid_hourly_rate(self):
        invalid_data = self.lawyer_data.copy()
        invalid_data['hourly_rate'] = '0.00'
        
        serializer = LawyerSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class MandateSerializerTest(TestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin3',
            email='admin3@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.client = TestDataFactory.create_client('Test Client', 'client@test.com')
        self.lawyer = TestDataFactory.create_lawyer('Test Lawyer', 'lawyer@test.com', Decimal('400.00'))
        
        self.mandate_data = {
            'name': 'Test Mandate',
            'description': 'Test description',
            'client': self.client.id,
            'lawyers': [self.lawyer.id],
            'due_date': date.today() + timedelta(days=30),
            'cost_ceiling': '50000.00',
            'is_active': True
        }
        self.mandate = TestDataFactory.create_mandate(
            name='Test Mandate',
            client=self.client,
            due_date=date.today() + timedelta(days=30),
            cost_ceiling=Decimal('50000.00'),
            is_active=True
        )
        self.mandate.lawyers.add(self.lawyer)

    def test_mandate_serialization(self):
        serializer = MandateSerializer(instance=self.mandate)
        data = serializer.data
        
        self.assertEqual(data['name'], 'Test Mandate')
        self.assertEqual(data['client_name'], 'Test Client')
        self.assertEqual(data['is_active'], True)
        self.assertEqual(data['lawyers_names'], ['Test Lawyer'])

    def test_mandate_deserialization(self):
        serializer = MandateSerializer(data=self.mandate_data)
        self.assertTrue(serializer.is_valid())
        
        mandate = serializer.save()
        self.assertEqual(mandate.name, 'Test Mandate')
        self.assertEqual(mandate.client, self.client)
        self.assertTrue(mandate.is_active)

    def test_mandate_detail_serializer(self):
        # Create a time entry using factory
        time_entry = TestDataFactory.create_time_entry(
            mandate=self.mandate,
            lawyer=self.lawyer,
            hours=Decimal('3.5'),
            entry_date=date.today(),
            description='Test work'
        )
        
        serializer = MandateDetailSerializer(instance=self.mandate)
        data = serializer.data
        
        self.assertEqual(len(data['time_entries']), 1)
        self.assertEqual(data['time_entries'][0]['hours'], '3.50')


class TimeEntrySerializerTest(TestCase):
    def setUp(self):
        # Create admin user for authentication
        self.admin_user = User.objects.create_user(
            username='testadmin4',
            email='admin4@test.com',
            password='testpass123',
            role='admin'
        )
        
        self.client = TestDataFactory.create_client('Test Client', 'client@test.com')
        self.lawyer = TestDataFactory.create_lawyer('Test Lawyer', 'lawyer@test.com', Decimal('400.00'))
        self.mandate = TestDataFactory.create_mandate(
            name='Test Mandate',
            client=self.client,
            due_date=date.today() + timedelta(days=30),
            is_active=True
        )
        self.mandate.lawyers.add(self.lawyer)
        
        self.time_entry_data = {
            'mandate': self.mandate.id,
            'lawyer': self.lawyer.id,
            'date': date.today(),
            'hours': '4.5',
            'description': 'Legal research'
        }
        self.time_entry = TestDataFactory.create_time_entry(
            mandate=self.mandate,
            lawyer=self.lawyer,
            hours=Decimal('4.5'),
            entry_date=date.today(),
            description='Legal research'
        )

    def test_time_entry_serialization(self):
        serializer = TimeEntrySerializer(instance=self.time_entry)
        data = serializer.data
        
        self.assertEqual(data['mandate_name'], 'Test Mandate')
        self.assertEqual(data['lawyer_name'], 'Test Lawyer')
        self.assertEqual(data['hours'], '4.50')
        self.assertEqual(data['cost'], self.time_entry.cost)

    def test_time_entry_deserialization(self):
        serializer = TimeEntrySerializer(data=self.time_entry_data)
        self.assertTrue(serializer.is_valid())
        
        time_entry = serializer.save()
        self.assertEqual(time_entry.mandate, self.mandate)
        self.assertEqual(time_entry.lawyer, self.lawyer)
        self.assertEqual(time_entry.hours, Decimal('4.5'))

    def test_time_entry_validation_lawyer_not_assigned(self):
        # Create a lawyer not assigned to the mandate
        unassigned_lawyer = TestDataFactory.create_lawyer(
            'Unassigned Lawyer', 'unassigned@test.com', Decimal('350.00')
        )
        
        invalid_data = self.time_entry_data.copy()
        invalid_data['lawyer'] = unassigned_lawyer.id
        
        serializer = TimeEntrySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('The selected lawyer is not assigned to this mandate', 
                     str(serializer.errors))

    def test_time_entry_invalid_hours(self):
        invalid_data = self.time_entry_data.copy()
        invalid_data['hours'] = '0.00'
        
        serializer = TimeEntrySerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())