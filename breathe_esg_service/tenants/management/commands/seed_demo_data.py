"""
Management command: seed_demo_data
Seeds Acme Corp tenant with realistic mixed-schema demo data.
"""
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed Breathe ESG demo data for Acme Corp'

    def handle(self, *args, **options):
        from tenants.models import Tenant
        from users.models import User
        from ingestion.models import IngestionJob
        from records.models import UtilityRecord, TravelRecord
        from audit.models import AuditLog

        self.stdout.write('Seeding demo data...')

        # ── Tenant ──────────────────────────────────────────────────────────
        tenant, _ = Tenant.objects.get_or_create(
            slug='acme-corp', defaults={'name': 'Acme Corp'}
        )
        self.stdout.write(f'  Tenant: {tenant}')

        # ── Users ────────────────────────────────────────────────────────────
        analyst, created = User.objects.get_or_create(
            email='analyst@acme.com',
            defaults={'tenant': tenant, 'role': 'analyst'},
        )
        if created:
            analyst.set_password('demo1234')
            analyst.save()
        self.stdout.write(f'  analyst@acme.com {"created" if created else "exists"}')

        admin, created = User.objects.get_or_create(
            email='admin@acme.com',
            defaults={'tenant': tenant, 'role': 'admin'},
        )
        if created:
            admin.set_password('demo1234')
            admin.save()
        self.stdout.write(f'  admin@acme.com {"created" if created else "exists"}')

        # ── Utility Job ──────────────────────────────────────────────────────
        util_job = IngestionJob.objects.create(
            tenant=tenant, source_type='utility_csv', status='done',
            created_by=analyst, completed_at=timezone.now(),
        )

        # 5 standard US utility records (mixed statuses)
        standard_rows = [
            {
                'raw': {
                    'Account Number': 'ACCT-1001',
                    'Service Address': '100 Main St, Austin TX 78701',
                    'Billing Period Start': '2024-01-01',
                    'Billing Period End': '2024-01-31',
                    'Usage (kWh)': '45230',
                    'Demand (kW)': '120',
                    'Amount': '5427.60',
                },
                'status': 'approved',
                'kwh': Decimal('45230'),
                'start': date(2024, 1, 1),
            },
            {
                'raw': {
                    'Account Number': 'ACCT-1002',
                    'Service Address': '200 Elm Ave, Dallas TX 75201',
                    'Billing Period Start': '2024-02-01',
                    'Billing Period End': '2024-02-28',
                    'Usage (kWh)': '38750',
                    'Demand (kW)': '98',
                    'Amount': '4650.00',
                },
                'status': 'pending',
                'kwh': Decimal('38750'),
                'start': date(2024, 2, 1),
            },
            {
                'raw': {
                    'Account Number': 'ACCT-1003',
                    'Service Address': '300 Oak Blvd, Houston TX 77001',
                    'Billing Period Start': '2024-03-01',
                    'Billing Period End': '2024-03-31',
                    'Usage (kWh)': '1250000',
                    'Demand (kW)': '890',
                    'Amount': '150000.00',
                },
                'status': 'flagged',
                'flag_reason': 'Usage over 1,000,000 kWh — possible unit error',
                'kwh': Decimal('1250000'),
                'start': date(2024, 3, 1),
            },
            {
                'raw': {
                    'Account Number': 'ACCT-1004',
                    'Service Address': '400 Pine Rd, San Antonio TX 78201',
                    'Billing Period Start': '2024-04-01',
                    'Billing Period End': '2024-04-30',
                    'Usage (kWh)': '29100',
                    'Demand (kW)': '75',
                    'Amount': '3492.00',
                },
                'status': 'pending',
                'kwh': Decimal('29100'),
                'start': date(2024, 4, 1),
            },
            {
                'raw': {
                    'Account Number': 'ACCT-1005',
                    'Service Address': '500 Maple Dr, Fort Worth TX 76101',
                    'Billing Period Start': '2024-05-01',
                    'Billing Period End': '2024-05-31',
                    'Usage (kWh)': '52400',
                    'Demand (kW)': '145',
                    'Amount': '6288.00',
                },
                'status': 'approved',
                'kwh': Decimal('52400'),
                'start': date(2024, 5, 1),
            },
        ]
        for row in standard_rows:
            r = UtilityRecord.objects.create(
                tenant=tenant, job=util_job,
                schema_type='standard', scope='scope_2',
                activity_date=row['start'],
                normalized_value=row['kwh'],
                normalized_unit='kWh',
                description=f"Electricity — {row['raw']['Service Address']}",
                raw_data=row['raw'],
                status=row['status'],
                flag_reason=row.get('flag_reason'),
            )
            AuditLog.objects.create(
                tenant=tenant, user=analyst, action='created',
                record_source_type='utility', record_id=r.id, job=util_job,
            )

        # 5 India DISCOM billing records (different schema — different raw_data keys)
        discom_rows = [
            {
                'raw': {
                    'Consumer Number': 'DISCOM-2001',
                    'DISCOM': 'BESCOM',
                    'Tariff Category': 'HT Commercial',
                    'Service Address': 'Plot 12, Whitefield, Bangalore 560066',
                    'Billing Period Start': '2024-01-01',
                    'Billing Period End': '2024-01-31',
                    'Units Consumed (kWh)': '88400',
                    'Maximum Demand (kVA)': '310',
                    'Total Amount (INR)': '884000',
                },
                'status': 'approved',
                'kwh': Decimal('88400'),
                'start': date(2024, 1, 1),
            },
            {
                'raw': {
                    'Consumer Number': 'DISCOM-2002',
                    'DISCOM': 'TSSPDCL',
                    'Tariff Category': 'LT Industry',
                    'Service Address': 'Survey 45, Nacharam, Hyderabad 500076',
                    'Billing Period Start': '2024-02-01',
                    'Billing Period End': '2024-02-28',
                    'Units Consumed (kWh)': '62300',
                    'Maximum Demand (kVA)': '220',
                    'Total Amount (INR)': '623000',
                },
                'status': 'pending',
                'kwh': Decimal('62300'),
                'start': date(2024, 2, 1),
            },
            {
                'raw': {
                    'Consumer Number': 'DISCOM-2003',
                    'DISCOM': 'MSEDCL',
                    'Tariff Category': 'HT Industry',
                    'Service Address': 'MIDC Andheri East, Mumbai 400093',
                    'Billing Period Start': '2024-03-01',
                    'Billing Period End': '2024-03-31',
                    'Units Consumed (kWh)': '1500000',
                    'Maximum Demand (kVA)': '1200',
                    'Total Amount (INR)': '15000000',
                },
                'status': 'flagged',
                'flag_reason': 'Usage over 1,000,000 kWh — possible unit error',
                'kwh': Decimal('1500000'),
                'start': date(2024, 3, 1),
            },
            {
                'raw': {
                    'Consumer Number': 'DISCOM-2004',
                    'DISCOM': 'KSEB',
                    'Tariff Category': 'LT Commercial',
                    'Service Address': 'MG Road, Kochi 682016',
                    'Billing Period Start': '2024-04-01',
                    'Billing Period End': '2024-04-30',
                    'Units Consumed (kWh)': '41200',
                    'Maximum Demand (kVA)': '180',
                    'Total Amount (INR)': '412000',
                },
                'status': 'pending',
                'kwh': Decimal('41200'),
                'start': date(2024, 4, 1),
            },
            {
                'raw': {
                    'Consumer Number': 'DISCOM-2005',
                    'DISCOM': 'WBSEDCL',
                    'Tariff Category': 'HT Commercial',
                    'Service Address': 'Salt Lake Sector V, Kolkata 700091',
                    'Billing Period Start': '2024-05-01',
                    'Billing Period End': '2024-05-31',
                    'Units Consumed (kWh)': '73800',
                    'Maximum Demand (kVA)': '260',
                    'Total Amount (INR)': '738000',
                },
                'status': 'approved',
                'kwh': Decimal('73800'),
                'start': date(2024, 5, 1),
            },
        ]
        for row in discom_rows:
            r = UtilityRecord.objects.create(
                tenant=tenant, job=util_job,
                schema_type='discom_india', scope='scope_2',
                activity_date=row['start'],
                normalized_value=row['kwh'],
                normalized_unit='kWh',
                description=f"Electricity — {row['raw']['Service Address']}",
                raw_data=row['raw'],
                status=row['status'],
                flag_reason=row.get('flag_reason'),
            )
            AuditLog.objects.create(
                tenant=tenant, user=analyst, action='created',
                record_source_type='utility', record_id=r.id, job=util_job,
            )

        util_job.records_success = 10
        util_job.records_failed = 0
        util_job.records_total = 10
        util_job.save()
        self.stdout.write('  10 UtilityRecords (5 standard + 5 DISCOM)')

        # ── Travel CSV Job ───────────────────────────────────────────────────
        travel_csv_job = IngestionJob.objects.create(
            tenant=tenant, source_type='travel_csv', status='done',
            created_by=analyst, completed_at=timezone.now(),
        )

        travelers = ['Alice Smith', 'Bob Jones', 'Carol White', 'Dave Brown']

        # 3 air — flagged (no distance)
        air_routes = [
            ('BOM', 'LHR'), ('DEL', 'JFK'), ('HYD', 'SIN'),
        ]
        for i, (orig, dest) in enumerate(air_routes):
            dep = date(2024, 3, 1) + timedelta(days=i * 7)
            arr = dep + timedelta(days=1)
            raw = {
                'Trip ID': f'TRIP-AIR-{1000 + i}',
                'Traveler': travelers[i % len(travelers)],
                'Travel Type': 'Air',
                'Origin': orig,
                'Destination': dest,
                'Departure Date': dep.strftime('%Y-%m-%d'),
                'Arrival Date': arr.strftime('%Y-%m-%d'),
                'Amount': str(800 + i * 150),
                'Currency': 'USD',
            }
            r = TravelRecord.objects.create(
                tenant=tenant, job=travel_csv_job,
                travel_type='air', schema_type='travel_csv', scope='scope_3',
                activity_date=dep,
                normalized_value=None, normalized_unit='km',
                description=f"air — {orig} to {dest}",
                raw_data=raw,
                status='flagged',
                flag_reason='Distance not computed — airport pair needs lookup',
            )
            AuditLog.objects.create(
                tenant=tenant, user=analyst, action='created',
                record_source_type='travel', record_id=r.id, job=travel_csv_job,
            )

        # 3 hotel — pending
        hotel_cities = [
            ('London', 'LHR', 3), ('New York', 'JFK', 4), ('Singapore', 'SIN', 2),
        ]
        for i, (city, code, nights) in enumerate(hotel_cities):
            dep = date(2024, 3, 2) + timedelta(days=i * 7)
            arr = dep + timedelta(days=nights)
            raw = {
                'Trip ID': f'TRIP-HTL-{2000 + i}',
                'Traveler': travelers[i % len(travelers)],
                'Travel Type': 'Hotel',
                'Origin': code,
                'Destination': code,
                'Departure Date': dep.strftime('%Y-%m-%d'),
                'Arrival Date': arr.strftime('%Y-%m-%d'),
                'Amount': str(200 * nights),
                'Currency': 'USD',
            }
            r = TravelRecord.objects.create(
                tenant=tenant, job=travel_csv_job,
                travel_type='hotel', schema_type='travel_csv', scope='scope_3',
                activity_date=dep,
                normalized_value=Decimal(str(nights)), normalized_unit='nights',
                description=f"hotel — {code} to {code}",
                raw_data=raw,
                status='pending',
            )
            AuditLog.objects.create(
                tenant=tenant, user=analyst, action='created',
                record_source_type='travel', record_id=r.id, job=travel_csv_job,
            )

        # 2 car — pending
        car_routes = [('Austin', 'Houston'), ('Dallas', 'Fort Worth')]
        for i, (orig, dest) in enumerate(car_routes):
            dep = date(2024, 4, 1) + timedelta(days=i * 3)
            raw = {
                'Trip ID': f'TRIP-CAR-{3000 + i}',
                'Traveler': travelers[i % len(travelers)],
                'Travel Type': 'Car',
                'Origin': orig,
                'Destination': dest,
                'Departure Date': dep.strftime('%Y-%m-%d'),
                'Arrival Date': dep.strftime('%Y-%m-%d'),
                'Amount': str(80 + i * 20),
                'Currency': 'USD',
            }
            r = TravelRecord.objects.create(
                tenant=tenant, job=travel_csv_job,
                travel_type='car', schema_type='travel_csv', scope='scope_3',
                activity_date=dep,
                normalized_value=None, normalized_unit='km',
                description=f"car — {orig} to {dest}",
                raw_data=raw,
                status='pending',
            )
            AuditLog.objects.create(
                tenant=tenant, user=analyst, action='created',
                record_source_type='travel', record_id=r.id, job=travel_csv_job,
            )

        # 2 rail — pending
        rail_routes = [('Mumbai', 'Pune'), ('Delhi', 'Agra')]
        for i, (orig, dest) in enumerate(rail_routes):
            dep = date(2024, 4, 10) + timedelta(days=i * 4)
            raw = {
                'Trip ID': f'TRIP-RAIL-{4000 + i}',
                'Traveler': travelers[i % len(travelers)],
                'Travel Type': 'Rail',
                'Origin': orig,
                'Destination': dest,
                'Departure Date': dep.strftime('%Y-%m-%d'),
                'Arrival Date': dep.strftime('%Y-%m-%d'),
                'Amount': str(30 + i * 10),
                'Currency': 'INR',
            }
            r = TravelRecord.objects.create(
                tenant=tenant, job=travel_csv_job,
                travel_type='rail', schema_type='travel_csv', scope='scope_3',
                activity_date=dep,
                normalized_value=None, normalized_unit='km',
                description=f"rail — {orig} to {dest}",
                raw_data=raw,
                status='pending',
            )
            AuditLog.objects.create(
                tenant=tenant, user=analyst, action='created',
                record_source_type='travel', record_id=r.id, job=travel_csv_job,
            )

        travel_csv_job.records_success = 10
        travel_csv_job.records_failed = 0
        travel_csv_job.records_total = 10
        travel_csv_job.save()
        self.stdout.write('  10 TravelRecords (3 air + 3 hotel + 2 car + 2 rail)')

        # ── Travel API Job (Concur) ──────────────────────────────────────────
        travel_api_job = IngestionJob.objects.create(
            tenant=tenant, source_type='travel_api', status='done',
            created_by=analyst, completed_at=timezone.now(),
        )

        concur_segments = [
            {
                'tripId': 'CONCUR-5001',
                'type': 'Air',
                'traveler': {'firstName': 'Alice', 'lastName': 'Smith'},
                'origin': 'BOM',
                'destination': 'SFO',
                'departureDate': '2024-05-10',
                'arrivalDate': '2024-05-11',
                'amount': 1250.00,
                'currency': 'USD',
                'confirmationNumber': 'AI9981',
                'vendorName': 'United Airlines',
            },
            {
                'tripId': 'CONCUR-5002',
                'type': 'Air',
                'traveler': {'firstName': 'Bob', 'lastName': 'Jones'},
                'origin': 'DEL',
                'destination': 'CDG',
                'departureDate': '2024-05-15',
                'arrivalDate': '2024-05-15',
                'amount': 980.00,
                'currency': 'EUR',
                'confirmationNumber': 'AI2245',
                'vendorName': 'Air France',
            },
            {
                'tripId': 'CONCUR-5003',
                'type': 'Air',
                'traveler': {'firstName': 'Carol', 'lastName': 'White'},
                'origin': 'HYD',
                'destination': 'DXB',
                'departureDate': '2024-05-20',
                'arrivalDate': '2024-05-20',
                'amount': 420.00,
                'currency': 'USD',
                'confirmationNumber': 'EK8871',
                'vendorName': 'Emirates',
            },
        ]

        for seg in concur_segments:
            dep = date(2024, 5, int(seg['departureDate'].split('-')[2]))
            orig = seg['origin']
            dest = seg['destination']
            r = TravelRecord.objects.create(
                tenant=tenant, job=travel_api_job,
                travel_type='air', schema_type='concur_api', scope='scope_3',
                activity_date=dep,
                normalized_value=None, normalized_unit='km',
                description=f"air — {orig} to {dest}",
                raw_data=seg,
                status='flagged',
                flag_reason='Distance not computed — airport pair needs lookup',
            )
            AuditLog.objects.create(
                tenant=tenant, user=analyst, action='created',
                record_source_type='travel', record_id=r.id, job=travel_api_job,
            )

        travel_api_job.records_success = 3
        travel_api_job.records_failed = 0
        travel_api_job.records_total = 3
        travel_api_job.save()
        self.stdout.write('  3 TravelRecords (Concur API / air)')

        self.stdout.write(self.style.SUCCESS('\nDemo data seeded successfully!'))
        self.stdout.write('  analyst@acme.com / demo1234')
        self.stdout.write('  admin@acme.com   / demo1234')
