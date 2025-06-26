from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from decimal import Decimal
from core.models import Client, Lawyer, Mandate, TimeEntry


class Command(BaseCommand):
    help = 'Populate database with test data for API testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            TimeEntry.objects.all().delete()
            Mandate.objects.all().delete()
            Client.objects.all().delete()
            Lawyer.objects.all().delete()

        with transaction.atomic():
            self.stdout.write('Creating test data...')
            
            # Create clients
            clients = [
                Client.objects.create(
                    name="Tech Solutions Inc.",
                    email="contact@techsolutions.com",
                    phone="555-0101",
                    address="123 Tech Street, Silicon Valley, CA 94000"
                ),
                Client.objects.create(
                    name="Green Energy Corp",
                    email="legal@greenenergy.com",
                    phone="555-0102",
                    address="456 Renewable Ave, Austin, TX 78701"
                ),
                Client.objects.create(
                    name="Healthcare Partners LLC",
                    email="info@healthcarepartners.com",
                    phone="555-0103",
                    address="789 Medical Drive, Boston, MA 02101"
                ),
                Client.objects.create(
                    name="Retail Giants Co",
                    email="legal@retailgiants.com",
                    phone="555-0104",
                    address="321 Commerce Blvd, Chicago, IL 60601"
                ),
            ]

            # Create lawyers
            lawyers = [
                Lawyer.objects.create(
                    name="Sarah Johnson",
                    email="sarah.johnson@lawfirm.com",
                    phone="555-0201",
                    hourly_rate=Decimal('450.00')
                ),
                Lawyer.objects.create(
                    name="Michael Chen",
                    email="michael.chen@lawfirm.com",
                    phone="555-0202",
                    hourly_rate=Decimal('380.00')
                ),
                Lawyer.objects.create(
                    name="Emily Rodriguez",
                    email="emily.rodriguez@lawfirm.com",
                    phone="555-0203",
                    hourly_rate=Decimal('420.00')
                ),
                Lawyer.objects.create(
                    name="David Thompson",
                    email="david.thompson@lawfirm.com",
                    phone="555-0204",
                    hourly_rate=Decimal('500.00')
                ),
                Lawyer.objects.create(
                    name="Lisa Wang",
                    email="lisa.wang@lawfirm.com",
                    phone="555-0205",
                    hourly_rate=Decimal('360.00')
                ),
            ]

            # Create mandates with different statuses
            today = date.today()
            
            mandates = [
                # Active mandates (due in future)
                Mandate.objects.create(
                    name="Software Licensing Agreement",
                    description="Review and negotiate software licensing terms for enterprise deployment",
                    client=clients[0],
                    due_date=today + timedelta(days=30),
                    cost_ceiling=Decimal('25000.00'),
                    is_active=True
                ),
                Mandate.objects.create(
                    name="Intellectual Property Protection",
                    description="Patent filing and trademark registration for new products",
                    client=clients[0],
                    due_date=today + timedelta(days=45),
                    cost_ceiling=Decimal('40000.00'),
                    is_active=True
                ),
                Mandate.objects.create(
                    name="Renewable Energy Contracts",
                    description="Draft and review contracts for solar farm development",
                    client=clients[1],
                    due_date=today + timedelta(days=60),
                    cost_ceiling=Decimal('75000.00'),
                    is_active=True
                ),
                Mandate.objects.create(
                    name="Healthcare Compliance Audit",
                    description="Ensure compliance with HIPAA and state healthcare regulations",
                    client=clients[2],
                    due_date=today + timedelta(days=21),
                    cost_ceiling=Decimal('30000.00'),
                    is_active=True
                ),
                Mandate.objects.create(
                    name="Retail Acquisition Due Diligence",
                    description="Legal due diligence for acquisition of regional retail chain",
                    client=clients[3],
                    due_date=today + timedelta(days=14),
                    cost_ceiling=Decimal('100000.00'),
                    is_active=True
                ),
                
                # Overdue but still active mandates
                Mandate.objects.create(
                    name="Employment Contract Review",
                    description="Review executive employment contracts and compensation packages",
                    client=clients[0],
                    due_date=today - timedelta(days=10),
                    cost_ceiling=Decimal('15000.00'),
                    is_active=True
                ),
                Mandate.objects.create(
                    name="Environmental Impact Assessment",
                    description="Legal review of environmental impact studies",
                    client=clients[1],
                    due_date=today - timedelta(days=5),
                    cost_ceiling=Decimal('20000.00'),
                    is_active=True
                ),
                
                # Completed/inactive mandates
                Mandate.objects.create(
                    name="Corporate Restructuring",
                    description="Complete corporate restructuring and subsidiary formation",
                    client=clients[2],
                    due_date=today - timedelta(days=30),
                    cost_ceiling=Decimal('80000.00'),
                    is_active=False
                ),
            ]

            # Assign lawyers to mandates
            mandates[0].lawyers.set([lawyers[0], lawyers[1]])  # Software Licensing
            mandates[1].lawyers.set([lawyers[0], lawyers[3]])  # IP Protection
            mandates[2].lawyers.set([lawyers[2], lawyers[4]])  # Renewable Energy
            mandates[3].lawyers.set([lawyers[1], lawyers[2]])  # Healthcare Compliance
            mandates[4].lawyers.set([lawyers[3], lawyers[0]])  # Retail Acquisition
            mandates[5].lawyers.set([lawyers[1]])             # Employment Contract
            mandates[6].lawyers.set([lawyers[2]])             # Environmental Impact
            mandates[7].lawyers.set([lawyers[3], lawyers[4]])  # Corporate Restructuring

            # Create time entries for the last 3 months
            start_date = today - timedelta(days=90)
            current_date = start_date

            time_entries_data = [
                # Recent entries (this month)
                (mandates[0], lawyers[0], today - timedelta(days=2), Decimal('3.5'), "Contract review and markup"),
                (mandates[0], lawyers[1], today - timedelta(days=2), Decimal('2.0'), "Client meeting and strategy discussion"),
                (mandates[1], lawyers[0], today - timedelta(days=1), Decimal('4.0'), "Patent research and filing preparation"),
                (mandates[1], lawyers[3], today - timedelta(days=1), Decimal('2.5'), "Trademark search and analysis"),
                (mandates[2], lawyers[2], today - timedelta(days=3), Decimal('5.0'), "Contract drafting and negotiation"),
                (mandates[3], lawyers[1], today - timedelta(days=1), Decimal('3.0'), "Compliance documentation review"),
                (mandates[4], lawyers[3], today - timedelta(days=1), Decimal('6.0'), "Due diligence document review"),
                
                # Last month entries
                (mandates[0], lawyers[0], today - timedelta(days=15), Decimal('4.5'), "Initial contract analysis"),
                (mandates[0], lawyers[1], today - timedelta(days=18), Decimal('3.0'), "Vendor negotiations"),
                (mandates[1], lawyers[0], today - timedelta(days=20), Decimal('5.5'), "Patent application drafting"),
                (mandates[2], lawyers[2], today - timedelta(days=25), Decimal('4.0'), "Regulatory compliance research"),
                (mandates[2], lawyers[4], today - timedelta(days=22), Decimal('3.5'), "Environmental law consultation"),
                (mandates[3], lawyers[1], today - timedelta(days=28), Decimal('6.0'), "HIPAA compliance audit"),
                (mandates[3], lawyers[2], today - timedelta(days=26), Decimal('2.5'), "Policy review and updates"),
                (mandates[4], lawyers[3], today - timedelta(days=30), Decimal('8.0'), "Financial document analysis"),
                (mandates[5], lawyers[1], today - timedelta(days=35), Decimal('4.0'), "Executive contract negotiation"),
                
                # Two months ago entries
                (mandates[0], lawyers[0], today - timedelta(days=45), Decimal('3.0'), "Kickoff meeting and planning"),
                (mandates[1], lawyers[3], today - timedelta(days=50), Decimal('5.0'), "IP portfolio assessment"),
                (mandates[2], lawyers[2], today - timedelta(days=55), Decimal('7.0'), "Energy contract template creation"),
                (mandates[3], lawyers[1], today - timedelta(days=60), Decimal('4.5'), "Healthcare regulation research"),
                (mandates[4], lawyers[3], today - timedelta(days=48), Decimal('6.5'), "Acquisition structure planning"),
                (mandates[6], lawyers[2], today - timedelta(days=40), Decimal('5.5'), "Environmental impact review"),
                (mandates[7], lawyers[3], today - timedelta(days=65), Decimal('12.0'), "Corporate restructuring planning"),
                (mandates[7], lawyers[4], today - timedelta(days=60), Decimal('8.0'), "Subsidiary formation documents"),
                (mandates[7], lawyers[3], today - timedelta(days=55), Decimal('10.0'), "Board resolutions and filings"),
            ]

            # Create time entries
            for mandate, lawyer, entry_date, hours, description in time_entries_data:
                TimeEntry.objects.create(
                    mandate=mandate,
                    lawyer=lawyer,
                    date=entry_date,
                    hours=hours,
                    description=description
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created test data:\n'
                    f'- {len(clients)} clients\n'
                    f'- {len(lawyers)} lawyers\n'
                    f'- {len(mandates)} mandates\n'
                    f'- {len(time_entries_data)} time entries'
                )
            )
            
            # Print some useful information
            self.stdout.write('\n' + '='*50)
            self.stdout.write('TEST DATA SUMMARY')
            self.stdout.write('='*50)
            
            active_mandates = [m for m in mandates if m.due_date >= today]
            overdue_mandates = [m for m in mandates if m.due_date < today]
            
            self.stdout.write(f'Active mandates (due date >= today): {len(active_mandates)}')
            self.stdout.write(f'Overdue mandates (due date < today): {len(overdue_mandates)}')
            
            self.stdout.write('\nSample API test calls:')
            self.stdout.write('1. Get all active mandates:')
            self.stdout.write(f'   GET /api/mandates/?due_date__gte={today}')
            
            self.stdout.write('2. Get overdue mandates:')
            self.stdout.write(f'   GET /api/mandates/?due_date__lt={today}')
            
            self.stdout.write('3. Get time entries for current month:')
            first_of_month = today.replace(day=1)
            self.stdout.write(f'   GET /api/time-entries/?date_from={first_of_month}&date_to={today}')
            
            self.stdout.write('4. Search mandates by client name:')
            self.stdout.write('   GET /api/mandates/?search=Tech Solutions')
            
            self.stdout.write('5. Get lawyer\'s time entries:')
            self.stdout.write(f'   GET /api/lawyers/{lawyers[0].id}/time_entries/')
            
            self.stdout.write('\nDatabase is ready for testing!')