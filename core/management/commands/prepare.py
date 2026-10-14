from django.conf import settings
from django.core.management.base import BaseCommand

from core.bootstrap import ensure_bootstrap_state
from core.schedules import ensure_default_schedules


class Command(BaseCommand):
    help = "Bootstrap state, default schedules, and webhook registration."

    def handle(self, *args, **options):
        ensure_bootstrap_state()
        ensure_default_schedules()
        if settings.PUBLIC_URL:
            from provider.webhook_register import ensure_webhook_registered

            ensure_webhook_registered()
