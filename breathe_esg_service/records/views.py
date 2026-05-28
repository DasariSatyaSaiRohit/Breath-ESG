"""
records/views.py

Phase 2 changes applied:
  E1  — SAP records included in list / detail / approve / flag / lock endpoints
  E7a — columns computed via single raw SQL (jsonb_object_keys), not Python loop
  E7b — select_related on all querysets to avoid FK N+1
  E11 — is_duplicate exposed in serialized output
"""
from django.db import connection
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SapRecord, TravelRecord, UtilityRecord
from .utils import (
    get_ip,
    parse_prefixed_id,
    get_record_by_prefixed_id,
    write_audit_log,
)

PAGE_SIZE = 50

# raw_data is write-once — never patched
ALLOWED_PATCH_FIELDS = {'normalized_value', 'normalized_unit', 'description', 'flag_reason'}

TRAVEL_SOURCE_TO_TYPE = {
    'travel_air':    'air',
    'travel_hotel':  'hotel',
    'travel_ground': 'car',
    'travel_rail':   'rail',
}


# ---------------------------------------------------------------------------
# Serializer helper
# ---------------------------------------------------------------------------

def serialize_record(record, source_type: str) -> dict:
    """
    id is always a prefixed string: "utility_42", "travel_7", "sap_3".
    raw_data included as-is — frontend derives column headers from its keys.
    is_duplicate exposed for the frontend badge (E11).
    """
    base = {
        'id':               f"{source_type}_{record.id}",
        'source_type':      source_type,
        'scope':            record.scope,
        'schema_type':      record.schema_type,
        'activity_date':    str(record.activity_date),
        'normalized_value': (
            str(record.normalized_value)
            if record.normalized_value is not None else None
        ),
        'normalized_unit':  record.normalized_unit,
        'description':      record.description,
        'raw_data':         record.raw_data,
        'status':           record.status,
        'flag_reason':      record.flag_reason,
        'is_locked':        record.is_locked,
        'is_duplicate':     record.is_duplicate,  # E11
        'edited_by':        record.edited_by.email if record.edited_by else None,
        'edited_at':        str(record.edited_at) if record.edited_at else None,
        'approved_by':      record.approved_by.email if record.approved_by else None,
        'approved_at':      str(record.approved_at) if record.approved_at else None,
        'created_at':       str(record.created_at),
    }
    if source_type == 'travel':
        base['travel_type'] = record.travel_type
    return base


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------

def _paginate(data, page, request):
    total = len(data)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = data[start:end]
    base = request.build_absolute_uri(request.path)
    return {
        'count':     total,
        'next':      f"{base}?page={page + 1}" if end < total else None,
        'previous':  f"{base}?page={page - 1}" if page > 1 else None,
        'page_data': page_data,
    }


# ---------------------------------------------------------------------------
# E7a — column extraction via single raw SQL (no Python loop, no N+1)
# ---------------------------------------------------------------------------

def _get_columns_sql(table_name: str, record_ids: list[int]) -> list[str]:
    """
    Use PostgreSQL's jsonb_object_keys() to extract all raw_data keys for
    the given record IDs in a single query.
    Returns a sorted list of unique keys.
    """
    if not record_ids:
        return []
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT DISTINCT jsonb_object_keys(raw_data)
            FROM   {table_name}
            WHERE  id = ANY(%s)
            ORDER  BY 1
            """,
            [record_ids],
        )
        return [row[0] for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# GET /api/records/
# ---------------------------------------------------------------------------

class RecordListView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        tenant = request.user.tenant
        source        = request.query_params.get('source', '')
        status_filter = request.query_params.get('status', '')
        date_from     = request.query_params.get('date_from', '')
        date_to       = request.query_params.get('date_to', '')
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            page = 1

        include_utility = not source or source == 'utility_electricity'
        include_travel  = not source or source.startswith('travel_')
        include_sap     = not source or source == 'sap_procurement'

        # ── Utility queryset ─────────────────────────────────────────────────
        # E7b: select_related to prevent FK N+1 on edited_by / approved_by
        utility_qs = UtilityRecord.objects.none()
        if include_utility:
            utility_qs = (
                UtilityRecord.objects
                .filter(tenant=tenant)
                .select_related('edited_by', 'approved_by')
            )
            if status_filter:
                utility_qs = utility_qs.filter(status=status_filter)
            if date_from:
                utility_qs = utility_qs.filter(activity_date__gte=date_from)
            if date_to:
                utility_qs = utility_qs.filter(activity_date__lte=date_to)

        # ── Travel queryset ───────────────────────────────────────────────────
        travel_qs = TravelRecord.objects.none()
        if include_travel:
            travel_qs = (
                TravelRecord.objects
                .filter(tenant=tenant)
                .select_related('edited_by', 'approved_by')
            )
            if status_filter:
                travel_qs = travel_qs.filter(status=status_filter)
            if date_from:
                travel_qs = travel_qs.filter(activity_date__gte=date_from)
            if date_to:
                travel_qs = travel_qs.filter(activity_date__lte=date_to)
            if source in TRAVEL_SOURCE_TO_TYPE:
                travel_qs = travel_qs.filter(travel_type=TRAVEL_SOURCE_TO_TYPE[source])

        # ── SAP queryset ──────────────────────────────────────────────────────
        sap_qs = SapRecord.objects.none()
        if include_sap:
            sap_qs = (
                SapRecord.objects
                .filter(tenant=tenant)
                .select_related('edited_by', 'approved_by')
            )
            if status_filter:
                sap_qs = sap_qs.filter(status=status_filter)
            if date_from:
                sap_qs = sap_qs.filter(activity_date__gte=date_from)
            if date_to:
                sap_qs = sap_qs.filter(activity_date__lte=date_to)

        # ── Serialise and merge ───────────────────────────────────────────────
        utility_list = [serialize_record(r, 'utility') for r in utility_qs]
        travel_list  = [serialize_record(r, 'travel')  for r in travel_qs]
        sap_list     = [serialize_record(r, 'sap')     for r in sap_qs]

        merged = utility_list + travel_list + sap_list
        # Default sort: most-recently-edited first, then created_at descending
        merged.sort(
            key=lambda r: (r['edited_at'] or '', r['created_at']),
            reverse=True,
        )

        paginated  = _paginate(merged, page, request)
        page_data  = paginated['page_data']

        # ── E7a: columns via single raw SQL per table ─────────────────────────
        # Only computed when a specific source is selected (otherwise no columns).
        columns: list[str] = []
        if source:
            if source == 'utility_electricity':
                ids = [int(r['id'].split('_', 1)[1]) for r in page_data]
                columns = _get_columns_sql('records_utilityrecord', ids)
            elif source.startswith('travel_'):
                ids = [int(r['id'].split('_', 1)[1]) for r in page_data]
                columns = _get_columns_sql('records_travelrecord', ids)
            elif source == 'sap_procurement':
                ids = [int(r['id'].split('_', 1)[1]) for r in page_data]
                columns = _get_columns_sql('records_saprecord', ids)

        return Response({
            'count':    paginated['count'],
            'next':     paginated['next'],
            'previous': paginated['previous'],
            'columns':  columns,
            'results':  page_data,
        })


# ---------------------------------------------------------------------------
# PATCH /api/records/{id}/
# ---------------------------------------------------------------------------

class RecordDetailView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['patch', 'head', 'options']

    def patch(self, request, pk):
        try:
            record, source_type = get_record_by_prefixed_id(pk, request.user.tenant)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)

        if record.is_locked:
            return Response({'detail': 'Record is locked.'}, status=403)

        payload = {k: v for k, v in request.data.items() if k in ALLOWED_PATCH_FIELDS}
        if not payload:
            return Response({'detail': 'No valid fields provided.'}, status=400)

        old_value = {
            'normalized_value': str(record.normalized_value) if record.normalized_value is not None else None,
            'normalized_unit':  record.normalized_unit,
            'description':      record.description,
            'flag_reason':      record.flag_reason,
        }

        for field, value in payload.items():
            setattr(record, field, value)
        record.edited_by = request.user
        record.edited_at = timezone.now()
        record.save()

        new_value = {
            'normalized_value': str(record.normalized_value) if record.normalized_value is not None else None,
            'normalized_unit':  record.normalized_unit,
            'description':      record.description,
            'flag_reason':      record.flag_reason,
        }

        write_audit_log(
            user=request.user, tenant=request.user.tenant,
            action='edited', record=record, source_type=source_type,
            old_value=old_value, new_value=new_value,
            ip_address=get_ip(request),
        )
        return Response(serialize_record(record, source_type))


# ---------------------------------------------------------------------------
# POST /api/records/{id}/approve/
# ---------------------------------------------------------------------------

class RecordApproveView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'head', 'options']

    def post(self, request, pk):
        try:
            record, source_type = get_record_by_prefixed_id(pk, request.user.tenant)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)

        if record.is_locked:
            return Response({'detail': 'Record is locked.'}, status=403)

        old_status = record.status
        record.status      = 'approved'
        record.approved_by = request.user
        record.approved_at = timezone.now()
        record.save()

        write_audit_log(
            user=request.user, tenant=request.user.tenant,
            action='approved', record=record, source_type=source_type,
            old_value={'status': old_status},
            new_value={'status': 'approved'},
            ip_address=get_ip(request),
        )
        return Response({
            'id':          f"{source_type}_{record.id}",
            'status':      record.status,
            'approved_by': request.user.email,
            'approved_at': str(record.approved_at),
        })


# ---------------------------------------------------------------------------
# POST /api/records/{id}/flag/
# ---------------------------------------------------------------------------

class RecordFlagView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'head', 'options']

    def post(self, request, pk):
        try:
            record, source_type = get_record_by_prefixed_id(pk, request.user.tenant)
        except ValueError as e:
            return Response({'detail': str(e)}, status=400)

        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'detail': 'reason is required.'}, status=400)
        if record.is_locked:
            return Response({'detail': 'Record is locked.'}, status=403)

        record.status      = 'flagged'
        record.flag_reason = reason
        record.save()

        write_audit_log(
            user=request.user, tenant=request.user.tenant,
            action='flagged', record=record, source_type=source_type,
            new_value={'flag_reason': reason},
            ip_address=get_ip(request),
        )
        return Response({
            'id':          f"{source_type}_{record.id}",
            'status':      record.status,
            'flag_reason': record.flag_reason,
        })


# ---------------------------------------------------------------------------
# POST /api/records/bulk-approve/
# ---------------------------------------------------------------------------

class BulkApproveView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'head', 'options']

    def post(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'ids must not be empty.'}, status=400)
        if len(ids) > 100:
            return Response({'detail': 'Cannot approve more than 100 records at once.'}, status=400)

        tenant       = request.user.tenant
        utility_ids  = []
        travel_ids   = []
        sap_ids      = []

        for raw_id in ids:
            try:
                source_type, record_id = parse_prefixed_id(str(raw_id))
                if source_type == 'utility':
                    utility_ids.append(record_id)
                elif source_type == 'travel':
                    travel_ids.append(record_id)
                elif source_type == 'sap':
                    sap_ids.append(record_id)
            except ValueError as e:
                return Response({'detail': str(e)}, status=400)

        utility_records = list(UtilityRecord.objects.filter(id__in=utility_ids, tenant=tenant))
        travel_records  = list(TravelRecord.objects.filter(id__in=travel_ids,  tenant=tenant))
        sap_records     = list(SapRecord.objects.filter(id__in=sap_ids,        tenant=tenant))

        all_records = utility_records + travel_records + sap_records
        if len(all_records) != len(ids):
            return Response(
                {'detail': 'One or more IDs not found or belong to another tenant.'},
                status=400,
            )

        if any(r.is_locked for r in all_records):
            return Response({'detail': 'One or more records are locked.'}, status=403)

        now = timezone.now()
        for r in all_records:
            r.status      = 'approved'
            r.approved_by = request.user
            r.approved_at = now
            r.save()

        write_audit_log(
            user=request.user, tenant=tenant,
            action='bulk_approved', record=None, source_type=None,
            new_value={'approved_ids': ids, 'count': len(ids)},
            ip_address=get_ip(request),
        )
        return Response({'approved_count': len(ids), 'failed_ids': []})


# ---------------------------------------------------------------------------
# POST /api/records/lock/   (admin only)
# ---------------------------------------------------------------------------

class RecordLockView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post', 'head', 'options']

    def post(self, request):
        if request.user.role != 'admin':
            return Response({'detail': 'Only admin users can lock records.'}, status=403)

        ids = request.data.get('ids', [])
        if not ids:
            return Response({'detail': 'ids must not be empty.'}, status=400)
        if len(ids) > 100:
            return Response({'detail': 'Cannot lock more than 100 records at once.'}, status=400)

        tenant      = request.user.tenant
        utility_ids = []
        travel_ids  = []
        sap_ids     = []

        for raw_id in ids:
            try:
                source_type, record_id = parse_prefixed_id(str(raw_id))
                if source_type == 'utility':
                    utility_ids.append(record_id)
                elif source_type == 'travel':
                    travel_ids.append(record_id)
                elif source_type == 'sap':
                    sap_ids.append(record_id)
            except ValueError as e:
                return Response({'detail': str(e)}, status=400)

        utility_records = list(UtilityRecord.objects.filter(id__in=utility_ids, tenant=tenant))
        travel_records  = list(TravelRecord.objects.filter(id__in=travel_ids,  tenant=tenant))
        sap_records     = list(SapRecord.objects.filter(id__in=sap_ids,        tenant=tenant))

        all_records = utility_records + travel_records + sap_records
        if len(all_records) != len(ids):
            return Response(
                {'detail': 'One or more IDs not found or belong to another tenant.'},
                status=400,
            )

        not_approved = [r for r in all_records if r.status != 'approved']
        if not_approved:
            return Response({'detail': 'Only approved records can be locked.'}, status=400)

        locked_count        = 0
        already_locked_count = 0

        type_map = [
            (utility_records, 'utility'),
            (travel_records,  'travel'),
            (sap_records,     'sap'),
        ]
        for records, src in type_map:
            for record in records:
                if record.is_locked:
                    already_locked_count += 1
                    continue
                record.is_locked = True
                record.save(update_fields=['is_locked'])
                write_audit_log(
                    user=request.user, tenant=tenant,
                    action='locked', record=record, source_type=src,
                    new_value={'is_locked': True},
                    ip_address=get_ip(request),
                )
                locked_count += 1

        return Response({
            'locked_count':         locked_count,
            'already_locked_count': already_locked_count,
        })
