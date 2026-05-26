from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import AuditLog

PAGE_SIZE = 50


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = AuditLog.objects.filter(tenant=request.user.tenant).order_by('-timestamp')

        date_from = request.query_params.get('date_from', '')
        date_to = request.query_params.get('date_to', '')
        action = request.query_params.get('action', '')

        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)
        if action:
            qs = qs.filter(action=action)

        total = qs.count()
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except ValueError:
            page = 1

        start = (page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        items = qs[start:end]

        results = []
        for log in items:
            results.append({
                'id': log.id,
                'user': log.user.email if log.user else None,
                'action': log.action,
                'record_source_type': log.record_source_type,
                'record_id': log.record_id,
                'job_id': log.job_id,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'timestamp': str(log.timestamp),
                'ip_address': log.ip_address,
            })

        base = request.build_absolute_uri(request.path)
        return Response({
            'count': total,
            'next': f"{base}?page={page + 1}" if end < total else None,
            'previous': f"{base}?page={page - 1}" if page > 1 else None,
            'results': results,
        })
