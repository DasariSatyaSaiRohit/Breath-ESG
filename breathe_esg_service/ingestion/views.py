import csv
import io
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
import requests as http_requests
from django.conf import settings

from .models import IngestionJob, RawRecord
from records.models import UtilityRecord, TravelRecord
from records.utils import (
    normalize_energy,
    parse_flexible_date,
    apply_flag_rules,
    write_audit_log,
    get_ip,
)
from records.emission_factors import get_electricity_factor, get_travel_factor


"""
ingestion/views/sap_upload.py

SAP Procurement CSV upload endpoint.
Follows the same synchronous inline-processing pattern as UtilityUploadView
and TravelUploadView (no Celery in this project).

POST /api/ingestion/sap/upload/
  - multipart/form-data field: file (.csv only, max 10 MB)
  - Returns 201 + job summary on success
  - Returns 400 on bad input
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AuditLog
from ingestion.models import IngestionJob, RawRecord
from records.emission_factors import get_sap_factor
from records.models import SapRecord
from records.parsers.sap_csv import parse_sap_csv
from records.utils import get_ip, write_audit_log

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Date parsing — SAP uses several formats
# ---------------------------------------------------------------------------

def _parse_document_date(raw: str):
    """
    Try common SAP date formats: DD.MM.YYYY, YYYY-MM-DD, MM/DD/YYYY.
    Returns a date object, or raises ValueError if nothing matches.
    """
    for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse SAP date: '{raw}'")


# ---------------------------------------------------------------------------
# Unit-to-kg conversion for emission factor application
# ---------------------------------------------------------------------------

_KG_FACTORS = {
    'kg': 1.0,
    'g': 0.001,
    't': 1000.0,
    'tonne': 1000.0,
    'tonnes': 1000.0,
    'ton': 1000.0,
    'lbs': 0.453592,
    'lb': 0.453592,
}


def _to_kg(quantity_str: str, unit_str: str) -> Decimal | None:
    """Convert a quantity + unit string to kg. Returns None if unrecognised."""
    try:
        qty = Decimal(quantity_str.replace(',', ''))
    except (InvalidOperation, AttributeError):
        return None
    factor = _KG_FACTORS.get(unit_str.strip().lower())
    if factor is None:
        return None
    return qty * Decimal(str(factor))


# ---------------------------------------------------------------------------
# Duplicate detection helper
# ---------------------------------------------------------------------------

def _mark_duplicates(new_records: list[SapRecord], job: IngestionJob) -> None:
    """
    For each newly created SapRecord, check whether a record with identical
    (tenant, source_type, raw_data) already exists from a *previous* job.
    Uses a single DB query per batch (no Python loop queries).

    Sets is_duplicate=True and duplicate_of=<original> on matches, then
    bulk-updates only the affected rows.
    """
    if not new_records:
        return

    raw_data_list = [r.raw_data for r in new_records]

    # Fetch all prior records for this tenant whose raw_data matches any of
    # the new records' raw_data (PostgreSQL JSONB @> operator via __contains).
    # We use a straightforward filter loop because Django's ORM doesn't
    # support OR-of-containment natively; we query once per distinct raw_data
    # value but batch the result.
    existing_map: dict[str, SapRecord] = {}
    for raw in raw_data_list:
        if not raw:
            continue
        existing_qs = SapRecord.objects.filter(
            tenant=job.tenant,
            source_type='sap_procurement',
            raw_data__contains=raw,
        ).exclude(job=job).order_by('created_at').first()
        if existing_qs:
            # Use a hashable key — convert dict to sorted tuple string
            key = str(sorted(raw.items()))
            existing_map[key] = existing_qs

    to_update = []
    for record in new_records:
        key = str(sorted((record.raw_data or {}).items()))
        original = existing_map.get(key)
        if original:
            record.is_duplicate = True
            record.duplicate_of = original
            to_update.append(record)

    if to_update:
        SapRecord.objects.bulk_update(to_update, ['is_duplicate', 'duplicate_of'])


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class SapCsvUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        tenant = request.user.tenant
        file_obj = request.FILES.get('file')

        if not file_obj:
            return Response({'detail': 'No file provided.'}, status=400)
        if not file_obj.name.lower().endswith('.csv'):
            return Response({'detail': 'File must be a .csv'}, status=400)
        if file_obj.size > MAX_FILE_SIZE:
            return Response({'detail': 'File exceeds 10 MB limit.'}, status=400)

        # Parse CSV bytes — raises ValueError on bad input
        try:
            rows = parse_sap_csv(file_obj.read())
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=400)

        job = IngestionJob.objects.create(
            tenant=tenant,
            source_type='travel_csv',   # closest existing choice; SAP jobs
            # are distinguished by the sap_records relation and audit log.
            status='running',
            created_by=request.user,
            raw_file=file_obj if file_obj.size <= MAX_FILE_SIZE else None,
            job_metadata={'source': 'sap_procurement', 'row_count': len(rows)},
        )

        created_records: list[SapRecord] = []

        for raw_row in rows:
            if not any(v.strip() for v in raw_row.values()):
                continue  # skip blank rows

            try:
                with transaction.atomic():
                    date_str = raw_row.get('Document_Date', '').strip()
                    activity_date = _parse_document_date(date_str)

                    material = raw_row.get('Material', '')
                    quantity_str = raw_row.get('Quantity', '0')
                    unit_str = raw_row.get('Unit', 'kg')

                    # E9b — apply emission factor
                    factor = get_sap_factor(material)
                    quantity_kg = _to_kg(quantity_str, unit_str)
                    if quantity_kg is not None and factor:
                        norm_value = round(float(quantity_kg) * factor, 4)
                        norm_decimal = Decimal(str(norm_value))
                    else:
                        norm_decimal = None

                    description = (
                        f"SAP — {material} "
                        f"({raw_row.get('Plant_Code', '')} / "
                        f"{raw_row.get('Cost_Center', '')})"
                    ).strip(' (/)').strip()

                    record = SapRecord.objects.create(
                        tenant=tenant,
                        job=job,
                        scope='scope_1',
                        schema_type='sap_csv',
                        source_type='sap_procurement',
                        activity_date=activity_date,
                        normalized_value=norm_decimal,
                        normalized_unit='kg CO2e',
                        description=description,
                        raw_data=raw_row,
                        status='pending',
                    )

                    write_audit_log(
                        user=request.user,
                        tenant=tenant,
                        action='created',
                        record=record,
                        source_type='sap',
                        job=job,
                        ip_address=get_ip(request),
                    )

                    created_records.append(record)
                    job.records_success += 1

            except Exception as exc:
                RawRecord.objects.create(
                    tenant=tenant,
                    job=job,
                    raw_data=raw_row,
                    parse_error=str(exc),
                )
                job.records_failed += 1

        # E11a — duplicate detection after all records are created
        _mark_duplicates(created_records, job)

        job.status = 'done'
        job.completed_at = timezone.now()
        job.records_total = job.records_success + job.records_failed
        job.save()

        return Response({
            'job_id': str(job.id),
            'status': job.status,
            'records_total': job.records_total,
            'records_success': job.records_success,
            'records_failed': job.records_failed,
            'error_message': job.error_message,
        }, status=201)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

TRAVEL_TYPE_MAP = {
    'air': 'air', 'Air': 'air',
    'hotel': 'hotel', 'Hotel': 'hotel',
    'car': 'car', 'Car': 'car',
    'rail': 'rail', 'Rail': 'rail',
}


def _job_response(job):
    return {
        'job_id': str(job.id),
        'status': job.status,
        'records_total': job.records_total,
        'records_success': job.records_success,
        'records_failed': job.records_failed,
        'error_message': job.error_message,
    }


def _read_csv(file_obj):
    content = file_obj.read()
    text = content.decode('utf-8-sig')
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return [], []
    headers = [h.strip() for h in rows[0]]
    return headers, rows[1:]


# ---------------------------------------------------------------------------
# POST /api/ingestion/utility/upload/
# ---------------------------------------------------------------------------

class UtilityUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        tenant = request.user.tenant
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file provided.'}, status=400)
        if not file_obj.name.lower().endswith('.csv'):
            return Response({'detail': 'File must be a .csv'}, status=400)
        if file_obj.size > MAX_FILE_SIZE:
            return Response({'detail': 'File exceeds 10 MB limit.'}, status=400)

        job = IngestionJob.objects.create(
            tenant=tenant,
            source_type='utility_csv',
            status='running',
            created_by=request.user,
            raw_file=file_obj,
        )

        file_obj.seek(0)
        headers, data_rows = _read_csv(file_obj)

        for row in data_rows:
            if not any(cell.strip() for cell in row):
                continue  # skip blank lines
            raw_row = dict(zip(headers, [c.strip() for c in row]))
            try:
                with transaction.atomic():
                    # Detect date/usage columns by trying common key names
                    date_val = (
                        raw_row.get('Billing Period Start')
                        or raw_row.get('billing_period_start')
                        or raw_row.get('Bill Date') or ''
                    )
                    usage_val = (
                        raw_row.get('Usage (kWh)')
                        or raw_row.get('Units Consumed (kWh)')
                        or raw_row.get('usage_kwh') or ''
                    )
                    end_val = (
                        raw_row.get('Billing Period End')
                        or raw_row.get('billing_period_end') or ''
                    )

                    start = parse_flexible_date(date_val)
                    end = parse_flexible_date(end_val) if end_val else None
                    norm_val, norm_unit = normalize_energy(usage_val, 'kWh')

                    # E9b — compute kg CO2e using electricity emission factor
                    country_code = raw_row.get('Country_Code', raw_row.get('country_code', 'DEFAULT'))
                    elec_factor = get_electricity_factor(country_code)
                    co2e_value = Decimal(str(round(float(norm_val) * elec_factor, 4)))

                    flag_reason = apply_flag_rules(
                        {
                            'normalized_value': norm_val,
                            'billing_period_start': start,
                            'billing_period_end': end,
                        },
                        'utility',
                    )

                    service_addr = (
                        raw_row.get('Service Address')
                        or raw_row.get('service_address') or ''
                    )

                    record = UtilityRecord.objects.create(
                        tenant=job.tenant,
                        job=job,
                        schema_type='standard',
                        scope='scope_2',
                        activity_date=start,
                        normalized_value=co2e_value,
                        normalized_unit='kg CO2e',
                        description=f"Electricity — {service_addr}",
                        raw_data=raw_row,
                        status='flagged' if flag_reason else 'pending',
                        flag_reason=flag_reason,
                    )
                    write_audit_log(
                        user=job.created_by,
                        tenant=job.tenant,
                        action='created',
                        record=record,
                        source_type='utility',
                        job=job,
                        ip_address=get_ip(request),
                    )
                    job.records_success += 1
            except Exception as e:
                RawRecord.objects.create(
                    tenant=job.tenant, job=job,
                    raw_data=raw_row, parse_error=str(e),
                )
                job.records_failed += 1

        job.status = 'done'
        job.completed_at = timezone.now()
        job.records_total = job.records_success + job.records_failed
        job.save()

        return Response(_job_response(job), status=201)


# ---------------------------------------------------------------------------
# POST /api/ingestion/travel/pull/
# ---------------------------------------------------------------------------

class TravelPullView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = request.user.tenant
        date_from = request.data.get('date_from', '').strip()
        date_to = request.data.get('date_to', '').strip()
        trip_id_filter = request.data.get('trip_id', None)

        if not date_from or not date_to:
            return Response({'detail': 'date_from and date_to are required.'}, status=400)
        try:
            df = parse_flexible_date(date_from)
            dt = parse_flexible_date(date_to)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)
        if df > dt:
            return Response({'detail': 'date_from must be <= date_to.'}, status=400)

        job = IngestionJob.objects.create(
            tenant=tenant,
            source_type='travel_api',
            status='running',
            created_by=request.user,
        )

        # Concur OAuth
        try:
            auth_resp = http_requests.post(
                f"{settings.CONCUR_BASE_URL}/oauth2/v0/token",
                data={
                    'client_id': settings.CONCUR_CLIENT_ID,
                    'client_secret': settings.CONCUR_CLIENT_SECRET,
                    'grant_type': 'client_credentials',
                },
                timeout=30,
            )
            if not auth_resp.ok:
                raise ValueError(auth_resp.text)
            token = auth_resp.json()['access_token']
        except Exception as e:
            job.status = 'failed'
            job.error_message = f"Concur auth failed: {e}"
            job.completed_at = timezone.now()
            job.save()
            return Response(_job_response(job), status=502)

        # Fetch trips
        try:
            params = {'startDate': date_from, 'endDate': date_to}
            if trip_id_filter:
                params['tripId'] = trip_id_filter
            trips_resp = http_requests.get(
                f"{settings.CONCUR_BASE_URL}/api/travel/trip/v1/list",
                headers={'Authorization': f"Bearer {token}"},
                params=params,
                timeout=60,
            )
            if not trips_resp.ok:
                raise ValueError(trips_resp.status_code)
            segments = trips_resp.json().get('segments', [])
        except Exception as e:
            job.status = 'failed'
            job.error_message = f"Concur API error: {e}"
            job.completed_at = timezone.now()
            job.save()
            return Response(_job_response(job), status=502)

        for seg in segments:
            raw_segment = dict(seg)
            try:
                with transaction.atomic():
                    raw_type = seg.get('type', '')
                    travel_type = TRAVEL_TYPE_MAP.get(raw_type)
                    if not travel_type:
                        raise ValueError(f"Unknown travel type: {raw_type!r}")

                    dep_str = seg.get('departureDate') or seg.get('checkInDate') or ''
                    arr_str = seg.get('arrivalDate') or seg.get('checkOutDate') or ''
                    activity_date = parse_flexible_date(dep_str)
                    origin = seg.get('origin', '')
                    destination = seg.get('destination', '')

                    if travel_type == 'hotel':
                        arr_date = parse_flexible_date(arr_str) if arr_str else None
                        nights = (arr_date - activity_date).days if arr_date else None
                        raw_qty = Decimal(str(nights)) if nights is not None else None
                        norm_unit = 'nights'
                    else:
                        raw_qty = None
                        norm_unit = 'km'

                    # E9b — apply travel emission factor → kg CO2e
                    cabin = raw_segment.get('cabin_class', 'DEFAULT')
                    factor = get_travel_factor(travel_type, cabin)
                    if raw_qty is not None and factor:
                        norm_val = Decimal(str(round(float(raw_qty) * factor, 4)))
                    else:
                        norm_val = None

                    flag_reason = apply_flag_rules(
                        {'normalized_value': raw_qty},   # flag rules use physical qty
                        'travel', travel_type,
                    )

                    record = TravelRecord.objects.create(
                        tenant=job.tenant, job=job,
                        travel_type=travel_type,
                        schema_type='concur_api',
                        scope='scope_3',
                        activity_date=activity_date,
                        normalized_value=norm_val,
                        normalized_unit='kg CO2e',
                        description=f"{travel_type} — {origin} to {destination}",
                        raw_data=raw_segment,
                        status='flagged' if flag_reason else 'pending',
                        flag_reason=flag_reason,
                    )
                    write_audit_log(
                        user=job.created_by, tenant=job.tenant,
                        action='created', record=record,
                        source_type='travel', job=job,
                        ip_address=get_ip(request),
                    )
                    job.records_success += 1
            except Exception as e:
                RawRecord.objects.create(
                    tenant=job.tenant, job=job,
                    raw_data=raw_segment, parse_error=str(e),
                )
                job.records_failed += 1

        job.status = 'done'
        job.completed_at = timezone.now()
        job.records_total = job.records_success + job.records_failed
        job.save()

        return Response(_job_response(job), status=201)


# ---------------------------------------------------------------------------
# POST /api/ingestion/travel/upload/
# ---------------------------------------------------------------------------

class TravelUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        tenant = request.user.tenant
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'detail': 'No file provided.'}, status=400)
        if not file_obj.name.lower().endswith('.csv'):
            return Response({'detail': 'File must be a .csv'}, status=400)
        if file_obj.size > MAX_FILE_SIZE:
            return Response({'detail': 'File exceeds 10 MB limit.'}, status=400)

        job = IngestionJob.objects.create(
            tenant=tenant,
            source_type='travel_csv',
            status='running',
            created_by=request.user,
            raw_file=file_obj,
        )

        file_obj.seek(0)
        headers, data_rows = _read_csv(file_obj)

        for row in data_rows:
            if not any(cell.strip() for cell in row):
                continue
            raw_row = dict(zip(headers, [c.strip() for c in row]))
            try:
                with transaction.atomic():
                    raw_type = raw_row.get('Travel Type', '').strip()
                    travel_type = TRAVEL_TYPE_MAP.get(raw_type)
                    if not travel_type:
                        raise ValueError(f"Unknown travel type: {raw_type!r}")

                    dep_str = raw_row.get('Departure Date', '').strip()
                    arr_str = raw_row.get('Arrival Date', '').strip()
                    activity_date = parse_flexible_date(dep_str)
                    origin = raw_row.get('Origin', '')
                    destination = raw_row.get('Destination', '')

                    if travel_type == 'hotel':
                        arr_date = parse_flexible_date(arr_str) if arr_str else None
                        nights = (arr_date - activity_date).days if arr_date else None
                        raw_qty = Decimal(str(nights)) if nights is not None else None
                        norm_unit = 'nights'
                    else:
                        raw_qty = None
                        norm_unit = 'km'

                    # E9b — apply travel emission factor → kg CO2e
                    cabin = raw_row.get('Cabin_Class', raw_row.get('cabin_class', 'DEFAULT'))
                    factor = get_travel_factor(travel_type, cabin)
                    if raw_qty is not None and factor:
                        norm_val = Decimal(str(round(float(raw_qty) * factor, 4)))
                    else:
                        norm_val = None

                    flag_reason = apply_flag_rules(
                        {'normalized_value': raw_qty},   # flag rules use physical qty
                        'travel', travel_type,
                    )

                    record = TravelRecord.objects.create(
                        tenant=job.tenant, job=job,
                        travel_type=travel_type,
                        schema_type='travel_csv',
                        scope='scope_3',
                        activity_date=activity_date,
                        normalized_value=norm_val,
                        normalized_unit='kg CO2e',
                        description=f"{travel_type} — {origin} to {destination}",
                        raw_data=raw_row,
                        status='flagged' if flag_reason else 'pending',
                        flag_reason=flag_reason,
                    )
                    write_audit_log(
                        user=job.created_by, tenant=job.tenant,
                        action='created', record=record,
                        source_type='travel', job=job,
                        ip_address=get_ip(request),
                    )
                    job.records_success += 1
            except Exception as e:
                RawRecord.objects.create(
                    tenant=job.tenant, job=job,
                    raw_data=raw_row, parse_error=str(e),
                )
                job.records_failed += 1

        job.status = 'done'
        job.completed_at = timezone.now()
        job.records_total = job.records_success + job.records_failed
        job.save()

        return Response(_job_response(job), status=201)


# ---------------------------------------------------------------------------
# GET /api/ingestion/jobs/{id}/
# ---------------------------------------------------------------------------

class JobDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            job = IngestionJob.objects.get(id=pk, tenant=request.user.tenant)
        except IngestionJob.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=404)
        return Response(_job_response(job))
