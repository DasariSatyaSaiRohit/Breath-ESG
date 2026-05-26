"""
Management command: seed_demo_data
Creates demo tenant, user, ingestion jobs, utility records, and travel records
so the analyst can log in and immediately see a populated review dashboard.
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from tenants.models import Tenant
from users.models import User
from ingestion.models import IngestionJob
from records.models import UtilityRecord, TravelRecord
from audit.models import AuditLog


STATUSES = ["pending", "approved", "flagged"]
TRAVEL_TYPES = ["air", "hotel", "car", "rail"]


class Command(BaseCommand):
    help = "Seed demo data for Breathe ESG — Acme Corp tenant"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # ---------- Tenant ----------
        tenant, _ = Tenant.objects.get_or_create(
            slug="acme-corp",
            defaults={"name": "Acme Corp"},
        )
        self.stdout.write(f"  Tenant: {tenant}")

        # ---------- User ----------
        user, created = User.objects.get_or_create(
            email="analyst@acme.com",
            defaults={"tenant": tenant, "role": "analyst"},
        )
        if created:
            user.set_password("demo1234")
            user.save()
        self.stdout.write(f"  User: {user.email} ({'created' if created else 'exists'})")

        # Also create an admin user for lock/unlock testing
        admin_user, created_admin = User.objects.get_or_create(
            email="admin@acme.com",
            defaults={"tenant": tenant, "role": "admin"},
        )
        if created_admin:
            admin_user.set_password("admin1234")
            admin_user.save()
        self.stdout.write(f"  Admin user: {admin_user.email} ({'created' if created_admin else 'exists'})")

        # ---------- Utility Job ----------
        utility_job = IngestionJob.objects.create(
            tenant=tenant,
            source_type="utility_csv",
            status="done",
            created_by=user,
            completed_at=timezone.now(),
            records_total=10,
            records_success=10,
            records_failed=0,
        )
        self.stdout.write(f"  IngestionJob (utility): {utility_job.id}")

        addresses = [
            "100 Main St, Austin TX",
            "200 Elm Ave, Dallas TX",
            "300 Oak Blvd, Houston TX",
            "400 Pine Rd, San Antonio TX",
            "500 Maple Dr, Fort Worth TX",
        ]

        for i in range(10):
            start = date(2024, 1, 1) + timedelta(days=30 * i)
            end = start + timedelta(days=28 + random.randint(0, 4))
            kwh = Decimal(str(random.randint(5000, 200000)))
            status = STATUSES[i % len(STATUSES)]
            r = UtilityRecord.objects.create(
                tenant=tenant,
                job=utility_job,
                scope="scope_2",
                activity_date=start,
                raw_value=kwh,
                raw_unit="kWh",
                normalized_value=kwh,
                normalized_unit="kWh",
                description=f"Electricity — {addresses[i % len(addresses)]}",
                status=status,
                flag_reason="Usage over 1,000,000 kWh — possible unit error" if status == "flagged" else None,
                account_number=f"ACCT-{1000 + i}",
                service_address=addresses[i % len(addresses)],
                billing_period_start=start,
                billing_period_end=end,
                usage_kwh=kwh,
                demand_kw=Decimal(str(random.randint(50, 500))),
                billed_amount=Decimal(str(round(float(kwh) * 0.12, 2))),
            )
            AuditLog.objects.create(
                tenant=tenant,
                user=user,
                action="created",
                record_type="utility",
                record_id=r.id,
                job=utility_job,
            )

        self.stdout.write("  10 UtilityRecords created")

        # ---------- Travel Job ----------
        travel_job = IngestionJob.objects.create(
            tenant=tenant,
            source_type="travel_csv",
            status="done",
            created_by=user,
            completed_at=timezone.now(),
            records_total=10,
            records_success=10,
            records_failed=0,
        )
        self.stdout.write(f"  IngestionJob (travel): {travel_job.id}")

        cities = ["NYC", "LAX", "ORD", "LHR", "CDG", "DXB", "SIN", "HKG", "SYD", "NRT"]
        travelers = ["Alice Smith", "Bob Jones", "Carol White", "Dave Brown"]

        for i in range(10):
            tt = TRAVEL_TYPES[i % len(TRAVEL_TYPES)]
            dep_date = date(2024, 3, 1) + timedelta(days=7 * i)
            arr_date = dep_date + timedelta(days=random.randint(1, 5))
            status = STATUSES[i % len(STATUSES)]
            origin = cities[i % len(cities)]
            dest = cities[(i + 1) % len(cities)]

            if tt == "air":
                norm_val = None
                norm_unit = "km"
                desc = f"Flight {origin} → {dest}"
                flag_reason = "Distance not computed — airport pair needs lookup" if status == "flagged" else None
            elif tt == "hotel":
                nights = (arr_date - dep_date).days
                norm_val = Decimal(str(nights))
                norm_unit = "nights"
                desc = f"Hotel — {dest}, {nights} nights"
                flag_reason = None
            else:
                norm_val = Decimal(str(random.randint(100, 1500)))
                norm_unit = "km"
                desc = f"{tt.capitalize()} — {origin} to {dest}"
                flag_reason = None

            r = TravelRecord.objects.create(
                tenant=tenant,
                job=travel_job,
                scope="scope_3",
                activity_date=dep_date,
                raw_value=Decimal(str(random.randint(200, 5000))),
                raw_unit="USD",
                normalized_value=norm_val,
                normalized_unit=norm_unit,
                description=desc,
                status=status,
                flag_reason=flag_reason,
                trip_id=f"TRIP-{2000 + i}",
                traveler=travelers[i % len(travelers)],
                travel_type=tt,
                origin=origin,
                destination=dest,
                departure_date=dep_date,
                arrival_date=arr_date,
                billed_amount=Decimal(str(random.randint(200, 5000))),
                currency="USD",
            )
            AuditLog.objects.create(
                tenant=tenant,
                user=user,
                action="created",
                record_type="travel",
                record_id=r.id,
                job=travel_job,
            )

        self.stdout.write("  10 TravelRecords created")
        self.stdout.write(self.style.SUCCESS("\nDemo data seeded successfully!"))
        self.stdout.write("  Login: analyst@acme.com / demo1234")
        self.stdout.write("  Admin: admin@acme.com / admin1234")
