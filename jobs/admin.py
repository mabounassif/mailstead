from django.contrib import admin, messages

from jobs.models import Job, Schedule, WorkerHeartbeat
from jobs.queue import enqueue


@admin.register(WorkerHeartbeat)
class WorkerHeartbeatAdmin(admin.ModelAdmin):
    list_display = ("id", "pid", "updated_at")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "state", "attempts", "run_after", "updated_at")
    list_filter = ("state", "kind")
    readonly_fields = ("payload", "last_error_redacted", "created_at", "updated_at")
    actions = ["retry_dead_jobs"]

    @admin.action(description="Retry dead jobs")
    def retry_dead_jobs(self, request, queryset):
        count = 0
        for job in queryset.filter(state=Job.State.DEAD):
            job.state = Job.State.QUEUED
            job.attempts = 0
            job.save(update_fields=["state", "attempts", "updated_at"])
            count += 1
        self.message_user(request, f"Requeued {count} jobs.", messages.SUCCESS)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "interval_seconds", "enabled", "last_enqueued_at")
