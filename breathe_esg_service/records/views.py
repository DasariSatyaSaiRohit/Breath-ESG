from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import UtilityRecord, TravelRecord
from .utils import (
    parse_prefixed_id,
    get_record_by_prefixed_id,
    get_columns_from_records,
    write_audit_log,
    get_ip,
)

PAGE_SIZE = 50

# raw_data is explicitly excluded — write-once, never patched
ALLOWED_PATCH_FIELDS = {'normalized_value', 'normalized_unit', 'description', 'flag_reason'}

TRAVEL_SOURCE_TO_TYPE = {
    'travel_air': 'air',
    'travel_hotel': 'hotel',
    'travel_ground': 'car',
    'travel_rail': 'rail',
}


def serialize_record(record, source_type: str) -> dict:
    """
    id is always returned as prefixed string: "utility_42" or "travel_7"
    raw_data is included as-is — frontend uses its keys as column headers.
    """
    base = {
        'id': f"{source_type}_{record.id}",
        'source_type': source_type,
        'scope': record.scope,
        'schema_type': record.schema_type,
        'activity_date': str(record.activity_date),
        'normalized_value': str(record.normalized_value) if record.normalized_value is not None else None,
        'normalized_unit': record.normalized_unit,
        'description': record.description,
        'raw_data': record.raw_data,
        'status': record.status,
        'flag_reason': record.flag_reason,
        'is_locked': record.is_locked,
        'edited_by': record.edited_by.email if record.edited_by else None,
        'edited_at': str(record.edited_at) if record.edited_at else None,
        'approved_by': record.approved_by.email if record.approved_by else None,
        'approved_at': str(record.approved_at) if record.approved_at else None,
        'created_at': str(record.created_at),
    }
    if source_type == 'travel':
        base['travel_type'] = record.travel_type
    return base


def _paginate(data, page, request):
    total = len(data)
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    page_data = data[start:end]
    base = request.build_absolute_uri(request.path)
    return {
        'count': total,
        'next': f"{base}?page={page + 1}" if end < total else None,
        'previous': f"{base}?page={page - 1}" if page > 1 else None,
        'page_data': page_data,
    }


# ---------------------------------------------------------------------------
# GET /api/records/
# ---------------------------------------------------------------------------

class RecordListView(APIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']

    def get(self, request):
        tenant = request.user.tenant
        source = request.query_params.get('source', '')
        status_filter = request.query_params.get('status', '')
        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            page = 1

        include_utility = not source or source == 'utility_electricity'
        include_travel = not source or source.startswith('travel_')

        utility_qs = UtilityRecord.objects.none()
        if include_utility:
            utility_qs = UtilityRecord.objects.filter(tenant=tenant)
            if status_filter:
                utility_qs = utility_qs.filter(status=status_filter)
            if date_from:
                utility_qs = utility_qs.filter(activity_date__gte=date_from)
            if date_to:
                utility_qs = utility_qs.filter(activity_date__lte=date_to)

        travel_qs = TravelRecord.objects.none()
        if include_travel:
            travel_qs = TravelRecord.objects.filter(tenant=tenant)
            if status_filter:
                travel_qs = travel_qs.filter(status=status_filter)
            if date_from:
                travel_qs = travel_qs.filter(activity_date__gte=date_from)
            if date_to:
                travel_qs = travel_qs.filter(activity_date__lte=date_to)
            if source in TRAVEL_SOURCE_TO_TYPE:
                travel_qs = travel_qs.filter(travel_type=TRAVEL_SOURCE_TO_TYPE[source])

        utility_serialized = [serialize_record(r, 'utility') for r in utility_qs]
        travel_serialized = [serialize_record(r, 'travel') for r in travel_qs]

        merged = utility_serialized + travel_serialized
        merged.sort(key=lambda r: r['activity_date'], reverse=True)

        paginated = _paginate(merged, page, request)
        page_data = paginated['page_data']

        # columns = union of raw_data keys across current page records
        # Only meaningful when a specific source is selected
        if source:
            # Get the actual model instances for this page to extract raw_data keys
            # We work from the serialized data since raw_data is included
            page_raw_keys = set()
            for item in page_data:
                for k in (item.get('raw_data') or {}).keys():
                    page_raw_keys.add(k)
            columns = sorted(page_raw_keys)
        else:
            columns = []

        return Response({
            'count': paginated['count'],
            'next': paginated['next'],
            'previous': paginated['previous'],
            'columns': columns,
            'results': page_data,
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

        # Explicitly strip raw_data and anything not in ALLOWED_PATCH_FIELDS
        payload = {k: v for k, v in request.data.items() if k in ALLOWED_PATCH_FIELDS}
        if not payload:
            return Response({'detail': 'No valid fields provided.'}, status=400)

        old_value = {
            'normalized_value': str(record.normalized_value) if record.normalized_value is not None else None,
            'normalized_unit': record.normalized_unit,
            'description': record.description,
            'flag_reason': record.flag_reason,
        }

        for field, value in payload.items():
            setattr(record, field, value)
        record.edited_by = request.user
        record.edited_at = timezone.now()
        record.save()

        new_value = {
            'normalized_value': str(record.normalized_value) if record.normalized_value is not None else None,
            'normalized_unit': record.normalized_unit,
            'description': record.description,
            'flag_reason': record.flag_reason,
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
        record.status = 'approved'
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
            'id': f"{source_type}_{record.id}",
            'status': record.status,
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

        record.status = 'flagged'
        record.flag_reason = reason
        record.save()

        write_audit_log(
            user=request.user, tenant=request.user.tenant,
            action='flagged', record=record, source_type=source_type,
            new_value={'flag_reason': reason},
            ip_address=get_ip(request),
        )
        return Response({
            'id': f"{source_type}_{record.id}",
            'status': record.status,
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

        tenant = request.user.tenant
        utility_ids = []
        travel_ids = []

        for raw_id in ids:
            try:
                source_type, record_id = parse_prefixed_id(str(raw_id))
                if source_type == 'utility':
                    utility_ids.append(record_id)
                else:
                    travel_ids.append(record_id)
            except ValueError as e:
                return Response({'detail': str(e)}, status=400)

        utility_records = list(UtilityRecord.objects.filter(id__in=utility_ids, tenant=tenant))
        travel_records = list(TravelRecord.objects.filter(id__in=travel_ids, tenant=tenant))

        if len(utility_records) + len(travel_records) != len(ids):
            return Response(
                {'detail': 'One or more IDs not found or belong to another tenant.'},
                status=400,
            )

        if any(r.is_locked for r in utility_records + travel_records):
            return Response({'detail': 'One or more records are locked.'}, status=403)

        now = timezone.now()
        for r in utility_records:
            r.status = 'approved'
            r.approved_by = request.user
            r.approved_at = now
            r.save()
        for r in travel_records:
            r.status = 'approved'
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
# POST /api/records/lock/
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

        tenant = request.user.tenant
        utility_ids = []
        travel_ids = []

        for raw_id in ids:
            try:
                source_type, record_id = parse_prefixed_id(str(raw_id))
                if source_type == 'utility':
                    utility_ids.append((record_id, raw_id))
                else:
                    travel_ids.append((record_id, raw_id))
            except ValueError as e:
                return Response({'detail': str(e)}, status=400)

        utility_records = list(UtilityRecord.objects.filter(
            id__in=[i for i, _ in utility_ids], tenant=tenant
        ))
        travel_records = list(TravelRecord.objects.filter(
            id__in=[i for i, _ in travel_ids], tenant=tenant
        ))

        total_fetched = len(utility_records) + len(travel_records)
        if total_fetched != len(ids):
            return Response(
                {'detail': 'One or more IDs not found or belong to another tenant.'},
                status=400,
            )

        # Only approved records can be locked
        not_approved = [r for r in utility_records + travel_records if r.status != 'approved']
        if not_approved:
            return Response(
                {'detail': 'Only approved records can be locked.'},
                status=400,
            )

        locked_count = 0
        already_locked_count = 0

        for record in utility_records:
            if record.is_locked:
                already_locked_count += 1
                continue
            record.is_locked = True
            record.save(update_fields=['is_locked'])
            write_audit_log(
                user=request.user, tenant=tenant,
                action='locked', record=record, source_type='utility',
                new_value={'is_locked': True},
                ip_address=get_ip(request),
            )
            locked_count += 1

        for record in travel_records:
            if record.is_locked:
                already_locked_count += 1
                continue
            record.is_locked = True
            record.save(update_fields=['is_locked'])
            write_audit_log(
                user=request.user, tenant=tenant,
                action='locked', record=record, source_type='travel',
                new_value={'is_locked': True},
                ip_address=get_ip(request),
            )
            locked_count += 1

        return Response({
            'locked_count': locked_count,
            'already_locked_count': already_locked_count,
        })
