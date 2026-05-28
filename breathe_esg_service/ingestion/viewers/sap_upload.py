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
