from django.db import models
from tenants.models import Tenant
from users.models import User


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('edited', 'Edited'),
        ('approved', 'Approved'),
        ('flagged', 'Flagged'),
        ('bulk_approved', 'Bulk Approved'),
        ('locked', 'Locked'),
    ]
    RECORD_SOURCE_TYPE_CHOICES = [
        ('utility', 'Utility'),
        ('travel', 'Travel'),
        ('sap', 'SAP'),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='audit_logs'
    )
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    record_source_type = models.CharField(
        max_length=20, choices=RECORD_SOURCE_TYPE_CHOICES,
        null=True, blank=True
    )
    # Plain integer — not a FK. record_source_type tells which table.
    # No referential integrity at DB level; enforced by blocking DELETE.
    record_id = models.IntegerField(null=True, blank=True)
    job = models.ForeignKey(
        'ingestion.IngestionJob', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='audit_logs'
    )
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"AuditLog {self.action} by {self.user} at {self.timestamp}"
