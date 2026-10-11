from django.core import serializers
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Export portal metadata (not mail blobs) as JSON."

    def handle(self, *args, **options):
        from accounts.models import Alias, Mailbox, User
        from enterprise.models import EntitlementCache, License
        from provider.models import ProviderSettings

        models = [User, Mailbox, Alias, License, EntitlementCache, ProviderSettings]
        for model in models:
            for obj in model.objects.all():
                self.stdout.write(serializers.serialize("json", [obj]))
