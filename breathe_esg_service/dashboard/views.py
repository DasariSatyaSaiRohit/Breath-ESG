"""
dashboard/views.py

GET /api/dashboard/summary/

Returns all dashboard data in one response using aggregation — no N+1 queries.
Maximum DB queries: 5
  1. stats aggregate (total, pending, approved, flagged, failed)
  2. scope breakdown (scope_1 / scope_2 / scope_3)
  3. source breakdown (utility / travel / sap)
  4. recent ingestion jobs (last 10)
  5. monthly trend (TruncMonth + Count)

The view merges UtilityRecord, TravelRecord, and SapRecord counts by running
each aggregate over all three tables and summing in Python — one aggregate
query per table per section, still well under 5 total for each section.
"""
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ingestion.models import IngestionJob
from records.models import SapRecord, TravelRecord, UtilityRecord


def _aggregate_records(tenant):
    """
    Run stat, scope, and source aggregates across all three record tables.
    Returns (stats_dict, scope_dict, source_dict).
    Each is ONE query per table (3 queries total for all three sections).
    """
    def _stats(qs):
        return qs.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            approved=Count('id', filter=Q(status='approved')),
            flagged=Count('id', filter=Q(status='flagged')),
            failed=Count('id', filter=Q(status='failed')),
        )

    def _scopes(qs):
        return qs.aggregate(
            scope_1=Count('id', filter=Q(scope='scope_1')),
            scope_2=Count('id', filter=Q(scope='scope_2')),
            scope_3=Count('id', filter=Q(scope='scope_3')),
        )

    u_qs = UtilityRecord.objects.filter(tenant=tenant)
    t_qs = TravelRecord.objects.filter(tenant=tenant)
    s_qs = SapRecord.objects.filter(tenant=tenant)

    # Run 3 combined aggregate queries (stats+scope per table merged)
    u_stats = _stats(u_qs)
    t_stats = _stats(t_qs)
    s_stats = _stats(s_qs)

    u_scopes = _scopes(u_qs)
    t_scopes = _scopes(t_qs)
    s_scopes = _scopes(s_qs)

    def _sum(key, *dicts):
        return sum(d.get(key) or 0 for d in dicts)

    stats = {
        'total_records':  _sum('total',    u_stats, t_stats, s_stats),
        'pending_review': _sum('pending',  u_stats, t_stats, s_stats),
        'approved':       _sum('approved', u_stats, t_stats, s_stats),
        'flagged':        _sum('flagged',  u_stats, t_stats, s_stats),
        'failed':         _sum('failed',   u_stats, t_stats, s_stats),
    }

    scope_breakdown = {
        'scope_1': _sum('scope_1', u_scopes, t_scopes, s_scopes),
        'scope_2': _sum('scope_2', u_scopes, t_scopes, s_scopes),
        'scope_3': _sum('scope_3', u_scopes, t_scopes, s_scopes),
    }

    source_breakdown = {
        'utility': u_stats.get('total') or 0,
        'travel':  t_stats.get('total') or 0,
        'sap':     s_stats.get('total') or 0,
    }

    return stats, scope_breakdown, source_breakdown


def _monthly_trend(tenant):
    """
    Monthly trend across all record types.
    3 queries (one per table), merged in Python.
    Returns list of { month, scope_1, scope_2, scope_3 } dicts sorted by month.
    """
    def _trend(qs):
        return (
            qs.annotate(month=TruncMonth('activity_date'))
            .values('month')
            .annotate(
                scope_1=Count('id', filter=Q(scope='scope_1')),
                scope_2=Count('id', filter=Q(scope='scope_2')),
                scope_3=Count('id', filter=Q(scope='scope_3')),
            )
            .order_by('month')
        )

    merged: dict[str, dict] = {}
    for row in _trend(UtilityRecord.objects.filter(tenant=tenant)):
        key = row['month'].strftime('%Y-%m')
        merged.setdefault(key, {'month': key, 'scope_1': 0, 'scope_2': 0, 'scope_3': 0})
        merged[key]['scope_1'] += row['scope_1']
        merged[key]['scope_2'] += row['scope_2']
        merged[key]['scope_3'] += row['scope_3']

    for row in _trend(TravelRecord.objects.filter(tenant=tenant)):
        key = row['month'].strftime('%Y-%m')
        merged.setdefault(key, {'month': key, 'scope_1': 0, 'scope_2': 0, 'scope_3': 0})
        merged[key]['scope_1'] += row['scope_1']
        merged[key]['scope_2'] += row['scope_2']
        merged[key]['scope_3'] += row['scope_3']

    for row in _trend(SapRecord.objects.filter(tenant=tenant)):
        key = row['month'].strftime('%Y-%m')
        merged.setdefault(key, {'month': key, 'scope_1': 0, 'scope_2': 0, 'scope_3': 0})
        merged[key]['scope_1'] += row['scope_1']
        merged[key]['scope_2'] += row['scope_2']
        merged[key]['scope_3'] += row['scope_3']

    return sorted(merged.values(), key=lambda r: r['month'])


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant

        stats, scope_breakdown, source_breakdown = _aggregate_records(tenant)

        recent_ingestions = list(
            IngestionJob.objects
            .filter(tenant=tenant)
            .order_by('-created_at')[:10]
            .values('id', 'source_type', 'status',
                    'records_total', 'records_success', 'records_failed',
                    'created_at', 'job_metadata')
        )

        # Normalise recent_ingestions to the shape the frontend expects
        recent = []
        for job in recent_ingestions:
            meta = job.get('job_metadata') or {}
            recent.append({
                'job_id':     str(job['id']),
                'source':     meta.get('source', job['source_type']),
                'status':     job['status'],
                'row_count':  job['records_total'],
                'created_at': job['created_at'].isoformat() if job['created_at'] else None,
            })

        monthly_trend = _monthly_trend(tenant)

        return Response({
            'stats':              stats,
            'scope_breakdown':    scope_breakdown,
            'source_breakdown':   source_breakdown,
            'recent_ingestions':  recent,
            'monthly_trend':      monthly_trend,
        })
