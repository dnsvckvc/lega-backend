from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Lawyer, Client, Mandate, TimeEntry
from decimal import Decimal
from datetime import date, timedelta
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo users and link them to lawyer profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users and data before creating demo users',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            User.objects.all().delete()
            Lawyer.objects.all().delete()
            Client.objects.all().delete()
            Mandate.objects.all().delete()
            TimeEntry.objects.all().delete()

        with transaction.atomic():
            self.stdout.write('Creating demo users and data...')
            
            # Create demo clients
            tech_client = Client.objects.create(
                name='TechCorp Industries',
                email='legal@techcorp.com',
                phone='555-0100',
                address='100 Innovation Drive, Silicon Valley, CA 94000'
            )
            
            retail_client = Client.objects.create(
                name='Retail Solutions Inc',
                email='contracts@retail-solutions.com',
                phone='555-0200',
                address='200 Commerce Street, New York, NY 10001'
            )

            # Create lawyers
            admin_lawyer = Lawyer.objects.create(
                name='Sarah Wilson',
                email='sarah.wilson@lawfirm.com',
                phone='555-0001',
                hourly_rate=Decimal('500.00')
            )
            
            regular_lawyer = Lawyer.objects.create(
                name='Michael Chen',
                email='michael.chen@lawfirm.com',
                phone='555-0002',
                hourly_rate=Decimal('400.00')
            )
            
            junior_lawyer = Lawyer.objects.create(
                name='Emma Rodriguez',
                email='emma.rodriguez@lawfirm.com',
                phone='555-0003',
                hourly_rate=Decimal('300.00')
            )

            # Create users
            # Admin lawyer user
            admin_user = User.objects.create_user(
                username='sarah.wilson',
                email='sarah.wilson@lawfirm.com',
                password='admin123',
                first_name='Sarah',
                last_name='Wilson',
                role='admin',
                lawyer_profile=admin_lawyer
            )
            
            # Regular lawyer users
            regular_user = User.objects.create_user(
                username='michael.chen',
                email='michael.chen@lawfirm.com',
                password='lawyer123',
                first_name='Michael',
                last_name='Chen',
                role='lawyer',
                lawyer_profile=regular_lawyer
            )
            
            junior_user = User.objects.create_user(
                username='emma.rodriguez',
                email='emma.rodriguez@lawfirm.com',
                password='lawyer123',
                first_name='Emma',
                last_name='Rodriguez',
                role='lawyer',
                lawyer_profile=junior_lawyer
            )

            # Create mandates
            mandate1 = Mandate.objects.create(
                name='TechCorp IP Protection',
                description='Intellectual property protection and patent filing for new technology',
                client=tech_client,
                due_date=date.today() + timedelta(days=45),
                cost_ceiling=Decimal('75000.00'),
                is_active=True
            )
            mandate1.lawyers.add(admin_lawyer, regular_lawyer)
            
            mandate2 = Mandate.objects.create(
                name='Retail Contract Review',
                description='Review and negotiate supplier contracts',
                client=retail_client,
                due_date=date.today() + timedelta(days=30),
                cost_ceiling=Decimal('25000.00'),
                is_active=True
            )
            mandate2.lawyers.add(regular_lawyer, junior_lawyer)
            
            # Overdue mandate for testing
            overdue_mandate = Mandate.objects.create(
                name='Legacy System Migration',
                description='Legal review for system migration project',
                client=tech_client,
                due_date=date.today() - timedelta(days=10),
                cost_ceiling=Decimal('50000.00'),
                is_active=True
            )
            overdue_mandate.lawyers.add(admin_lawyer)

            # Create some time entries
            TimeEntry.objects.create(
                mandate=mandate1,
                lawyer=admin_lawyer,
                date=date.today(),
                hours=Decimal('4.5'),
                description='Initial patent research and prior art analysis'
            )
            
            TimeEntry.objects.create(
                mandate=mandate1,
                lawyer=regular_lawyer,
                date=date.today() - timedelta(days=1),
                hours=Decimal('6.0'),
                description='Drafted patent application sections 1-3'
            )
            
            TimeEntry.objects.create(
                mandate=mandate2,
                lawyer=regular_lawyer,
                date=date.today() - timedelta(days=2),
                hours=Decimal('3.5'),
                description='Contract terms review and analysis'
            )
            
            TimeEntry.objects.create(
                mandate=mandate2,
                lawyer=junior_lawyer,
                date=date.today(),
                hours=Decimal('2.0'),
                description='Supplier agreement research'
            )

            self.stdout.write(
                self.style.SUCCESS(
                    'Successfully created demo users and data!\n\n'
                    'Admin User (full access):\n'
                    '  Email: sarah.wilson@lawfirm.com\n'
                    '  Password: admin123\n'
                    '  Role: Admin Lawyer\n\n'
                    'Regular User (limited access):\n'
                    '  Email: michael.chen@lawfirm.com\n'
                    '  Password: lawyer123\n'
                    '  Role: Regular Lawyer\n\n'
                    'Junior User (limited access):\n'
                    '  Email: emma.rodriguez@lawfirm.com\n'
                    '  Password: lawyer123\n'
                    '  Role: Regular Lawyer\n\n'
                    'Login at: POST /auth/login/\n'
                    'API Base URL: /api/\n'
                )
            )