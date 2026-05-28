"""
tenants/views.py

Provides the tenant configuration used by the frontend for UI localisation:
  - IANA timezone string
  - Date display format token (e.g. "DD/MM/YYYY")

GET /api/tenant/config/  →  { id, name, timezone, date_display_format }
"""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class TenantConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.tenant
        if tenant is None:
            return Response({'detail': 'No tenant associated with this user.'}, status=400)

        return Response({
            'id':                  str(tenant.id),
            'name':                tenant.name,
            'timezone':            tenant.timezone,
            'date_display_format': tenant.date_display_format,
        })
