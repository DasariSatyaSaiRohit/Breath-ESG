import uuid
from django.db import models
from tenants.models import Tenant
from users.models import User


class IngestionJob(models.Model):
    SOURCE_TYPE_CHOICES = [
        ("utility_csv", "Utility CSV"),
        ("travel_api", "Travel API"),
        ("travel_csv", "Travel CSV"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="ingestion_jobs")
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="ingestion_jobs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    raw_file = models.FileField(upload_to="ingestion/", null=True, blank=True)
    job_metadata = models.JSONField(default=dict)
    records_total = models.IntegerField(default=0)
    records_success = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source_type} job {self.id} [{self.status}]"


class RawRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(IngestionJob, on_delete=models.CASCADE, related_name="raw_records")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="raw_records")
    raw_data = models.JSONField()
    parse_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"RawRecord {self.id} [{self.job_id}]"
