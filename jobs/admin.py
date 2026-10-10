from django.contrib import admin

from jobs.models import WorkerHeartbeat


@admin.register(WorkerHeartbeat)
class WorkerHeartbeatAdmin(admin.ModelAdmin):
    list_display = ("id", "pid", "updated_at")
