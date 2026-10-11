from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "jobs"
    verbose_name = "Jobs"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from jobs.models import Schedule

        def ensure_schedules(sender, **kwargs):
            if sender.name != "jobs":
                return
            Schedule.objects.get_or_create(
                name="reconcile_received",
                defaults={"kind": "reconcile_received", "interval_seconds": 900, "payload": {}},
            )
            Schedule.objects.get_or_create(
                name="register_webhook",
                defaults={"kind": "register_webhook", "interval_seconds": 3600, "payload": {}},
            )

        post_migrate.connect(ensure_schedules, dispatch_uid="jobs_schedules")
