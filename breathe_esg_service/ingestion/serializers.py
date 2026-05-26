from rest_framework import serializers
from .models import IngestionJob


class IngestionJobSerializer(serializers.ModelSerializer):
    job_id = serializers.SerializerMethodField()

    class Meta:
        model = IngestionJob
        fields = [
            "job_id",
            "status",
            "records_total",
            "records_success",
            "records_failed",
            "error_message",
        ]

    def get_job_id(self, obj):
        return str(obj.id)
