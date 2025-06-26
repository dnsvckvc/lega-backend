"""
Test data factories for creating consistent test objects.
These factories can be used across different test files to create objects with realistic data.
"""

from decimal import Decimal
from datetime import date, timedelta
from .models import Client, Lawyer, Mandate, TimeEntry


class TestDataFactory:
    """Factory class for creating test data objects"""
    
    @staticmethod
    def create_client(name=None, email=None, **kwargs):
        """Create a test client with default or custom data"""
        defaults = {
            'name': name or 'Test Corporation',
            'email': email or 'contact@testcorp.com',
            'phone': '555-0123',
            'address': '123 Test Street, Test City, TC 12345'
        }
        defaults.update(kwargs)
        return Client.objects.create(**defaults)
    
    @staticmethod
    def create_lawyer(name=None, email=None, hourly_rate=None, **kwargs):
        """Create a test lawyer with default or custom data"""
        defaults = {
            'name': name or 'Test Lawyer',
            'email': email or 'lawyer@testfirm.com',
            'phone': '555-0456',
            'hourly_rate': hourly_rate or Decimal('400.00')
        }
        defaults.update(kwargs)
        return Lawyer.objects.create(**defaults)
    
    @staticmethod
    def create_mandate(client=None, name=None, due_date=None, is_active=True, **kwargs):
        """Create a test mandate with default or custom data"""
        if client is None:
            client = TestDataFactory.create_client()
        
        defaults = {
            'name': name or 'Test Mandate',
            'description': 'Test mandate description',
            'client': client,
            'due_date': due_date or (date.today() + timedelta(days=30)),
            'cost_ceiling': Decimal('50000.00'),
            'is_active': is_active
        }
        defaults.update(kwargs)
        return Mandate.objects.create(**defaults)
    
    @staticmethod
    def create_time_entry(mandate=None, lawyer=None, hours=None, entry_date=None, **kwargs):
        """Create a test time entry with default or custom data"""
        if mandate is None:
            mandate = TestDataFactory.create_mandate()
        if lawyer is None:
            lawyer = TestDataFactory.create_lawyer()
            mandate.lawyers.add(lawyer)
        
        defaults = {
            'mandate': mandate,
            'lawyer': lawyer,
            'date': entry_date or date.today(),
            'hours': hours or Decimal('4.0'),
            'description': 'Test work description'
        }
        defaults.update(kwargs)
        return TimeEntry.objects.create(**defaults)
    
    @classmethod
    def create_complete_scenario(cls):
        """Create a complete test scenario with related objects"""
        # Create clients
        client1 = cls.create_client('Tech Solutions Inc.', 'contact@techsolutions.com')
        client2 = cls.create_client('Green Energy Corp', 'legal@greenenergy.com')
        
        # Create lawyers
        lawyer1 = cls.create_lawyer('Sarah Johnson', 'sarah@lawfirm.com', Decimal('450.00'))
        lawyer2 = cls.create_lawyer('Michael Chen', 'michael@lawfirm.com', Decimal('380.00'))
        lawyer3 = cls.create_lawyer('Emily Rodriguez', 'emily@lawfirm.com', Decimal('420.00'))
        
        # Create mandates
        active_mandate = cls.create_mandate(
            client=client1,
            name='Software Licensing Agreement',
            due_date=date.today() + timedelta(days=30),
            is_active=True
        )
        active_mandate.lawyers.add(lawyer1, lawyer2)
        
        overdue_mandate = cls.create_mandate(
            client=client1,
            name='Employment Contract Review',
            due_date=date.today() - timedelta(days=10),
            is_active=True
        )
        overdue_mandate.lawyers.add(lawyer2)
        
        inactive_mandate = cls.create_mandate(
            client=client2,
            name='Corporate Restructuring',
            due_date=date.today() - timedelta(days=30),
            is_active=False
        )
        inactive_mandate.lawyers.add(lawyer3)
        
        # Create time entries
        cls.create_time_entry(
            mandate=active_mandate,
            lawyer=lawyer1,
            hours=Decimal('3.5'),
            entry_date=date.today()
        )
        cls.create_time_entry(
            mandate=active_mandate,
            lawyer=lawyer2,
            hours=Decimal('2.0'),
            entry_date=date.today() - timedelta(days=1)
        )
        cls.create_time_entry(
            mandate=overdue_mandate,
            lawyer=lawyer2,
            hours=Decimal('4.0'),
            entry_date=date.today() - timedelta(days=5)
        )
        
        return {
            'clients': [client1, client2],
            'lawyers': [lawyer1, lawyer2, lawyer3],
            'mandates': [active_mandate, overdue_mandate, inactive_mandate],
        }


# Convenience functions for specific test scenarios
def create_basic_test_data():
    """Create basic test data for simple tests"""
    client = TestDataFactory.create_client()
    lawyer = TestDataFactory.create_lawyer()
    mandate = TestDataFactory.create_mandate(client=client)
    mandate.lawyers.add(lawyer)
    time_entry = TestDataFactory.create_time_entry(mandate=mandate, lawyer=lawyer)
    
    return {
        'client': client,
        'lawyer': lawyer,
        'mandate': mandate,
        'time_entry': time_entry
    }


def create_filtering_test_data():
    """Create test data specifically for filtering tests"""
    # Create multiple clients
    tech_client = TestDataFactory.create_client('Tech Corp', 'tech@corp.com')
    law_client = TestDataFactory.create_client('Law Firm LLC', 'info@lawfirm.com')
    
    # Create multiple lawyers with different rates
    senior_lawyer = TestDataFactory.create_lawyer('Senior Partner', 'senior@law.com', Decimal('500.00'))
    junior_lawyer = TestDataFactory.create_lawyer('Junior Associate', 'junior@law.com', Decimal('300.00'))
    
    # Create mandates with different statuses and dates
    active_future = TestDataFactory.create_mandate(
        client=tech_client,
        name='Future Project',
        due_date=date.today() + timedelta(days=60),
        is_active=True
    )
    active_overdue = TestDataFactory.create_mandate(
        client=tech_client,
        name='Overdue Project',
        due_date=date.today() - timedelta(days=15),
        is_active=True
    )
    inactive_past = TestDataFactory.create_mandate(
        client=law_client,
        name='Completed Project',
        due_date=date.today() - timedelta(days=45),
        is_active=False
    )
    
    # Assign lawyers to mandates
    active_future.lawyers.add(senior_lawyer, junior_lawyer)
    active_overdue.lawyers.add(senior_lawyer)
    inactive_past.lawyers.add(junior_lawyer)
    
    # Create time entries across different dates
    TestDataFactory.create_time_entry(
        mandate=active_future,
        lawyer=senior_lawyer,
        hours=Decimal('8.0'),
        entry_date=date.today()
    )
    TestDataFactory.create_time_entry(
        mandate=active_overdue,
        lawyer=senior_lawyer,
        hours=Decimal('6.0'),
        entry_date=date.today() - timedelta(days=7)
    )
    TestDataFactory.create_time_entry(
        mandate=inactive_past,
        lawyer=junior_lawyer,
        hours=Decimal('10.0'),
        entry_date=date.today() - timedelta(days=60)
    )
    
    return {
        'clients': [tech_client, law_client],
        'lawyers': [senior_lawyer, junior_lawyer],
        'mandates': [active_future, active_overdue, inactive_past]
    }