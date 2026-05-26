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
                        normalized_value=norm_val,
                        normalized_unit=norm_unit,
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
                        norm_val = Decimal(str(nights)) if nights is not None else None
                        norm_unit = 'nights'
                    else:
                        norm_val = None
                        norm_unit = 'km'

                    flag_reason = apply_flag_rules(
                        {'normalized_value': norm_val},
                        'travel', travel_type,
                    )

                    record = TravelRecord.objects.create(
                        tenant=job.tenant, job=job,
                        travel_type=travel_type,
                        schema_type='concur_api',
                        scope='scope_3',
                        activity_date=activity_date,
                        normalized_value=norm_val,
                        normalized_unit=norm_unit,
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
                        norm_val = Decimal(str(nights)) if nights is not None else None
                        norm_unit = 'nights'
                    else:
                        norm_val = None
                        norm_unit = 'km'

                    flag_reason = apply_flag_rules(
                        {'normalized_value': norm_val},
                        'travel', travel_type,
                    )

                    record = TravelRecord.objects.create(
                        tenant=job.tenant, job=job,
                        travel_type=travel_type,
                        schema_type='travel_csv',
                        scope='scope_3',
                        activity_date=activity_date,
                        normalized_value=norm_val,
                        normalized_unit=norm_unit,
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
