from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("api/auth/", include("users.urls")),
    path("api/ingestion/", include("ingestion.urls")),
    path("api/records/", include("records.urls")),
    path("api/audit/", include("audit.urls")),
    path("api/tenant/", include("tenants.urls")),
    path("api/dashboard/", include("dashboard.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
