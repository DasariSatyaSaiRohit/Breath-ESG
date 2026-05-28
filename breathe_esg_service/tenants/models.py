import uuid
from django.db import models


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # E10a — timezone and date display format for per-tenant UI localisation
    timezone = models.CharField(
        max_length=64,
        default='UTC',
        help_text='IANA timezone string, e.g. Asia/Kolkata',
    )
    date_display_format = models.CharField(
        max_length=32,
        default='YYYY-MM-DD',
        help_text='UI date format token string, e.g. DD/MM/YYYY',
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
