from django.db import models


class UtilityRecord(models.Model):
    # IDENTITY
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE,
        related_name='utility_records'
    )
    job = models.ForeignKey(
        'ingestion.IngestionJob', on_delete=models.CASCADE,
        related_name='utility_records'
    )

    # CLASSIFICATION
    scope = models.CharField(max_length=20, default='scope_2')
    schema_type = models.CharField(max_length=50, default='standard')

    # NORMALIZED
    activity_date = models.DateField()
    normalized_value = models.DecimalField(
        max_digits=15, decimal_places=4, null=True
    )
    normalized_unit = models.CharField(max_length=50, default='kWh')
    description = models.TextField()

    # RAW — write-once, never updated after creation
    raw_data = models.JSONField(default=dict)

    # REVIEW STATE
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('flagged', 'Flagged'),
            ('failed', 'Failed'),
        ],
        default='pending',
    )
    flag_reason = models.TextField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)

    # AUDIT TRAIL
    edited_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='utility_edits'
    )
    edited_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='utility_approvals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-activity_date']

    def __str__(self):
        return f"UtilityRecord {self.id} [{self.status}]"


class TravelRecord(models.Model):
    # IDENTITY
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE,
        related_name='travel_records'
    )
    job = models.ForeignKey(
        'ingestion.IngestionJob', on_delete=models.CASCADE,
        related_name='travel_records'
    )

    # CLASSIFICATION
    scope = models.CharField(max_length=20, default='scope_3')
    travel_type = models.CharField(
        max_length=20,
        choices=[
            ('air', 'Air'),
            ('hotel', 'Hotel'),
            ('car', 'Car'),
            ('rail', 'Rail'),
        ],
    )
    schema_type = models.CharField(max_length=50, default='travel_csv')

    # NORMALIZED
    activity_date = models.DateField()
    normalized_value = models.DecimalField(
        max_digits=15, decimal_places=4, null=True
    )
    normalized_unit = models.CharField(max_length=50)
    description = models.TextField()

    # RAW — write-once, never updated after creation
    raw_data = models.JSONField(default=dict)

    # REVIEW STATE
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('flagged', 'Flagged'),
            ('failed', 'Failed'),
        ],
        default='pending',
    )
    flag_reason = models.TextField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)

    # AUDIT TRAIL
    edited_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='travel_edits'
    )
    edited_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='travel_approvals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-activity_date']

    def __str__(self):
        return f"TravelRecord {self.id} [{self.travel_type}] [{self.status}]"
