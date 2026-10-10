from django.db import models


class WorkerHeartbeat(models.Model):
    """Updated periodically by the background worker process."""

    pid = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        get_latest_by = "updated_at"
