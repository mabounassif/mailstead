from django.contrib import admin, messages

from provider.models import ProviderSettings
from provider.webhook_register import ensure_webhook_registered


@admin.register(ProviderSettings)
class ProviderSettingsAdmin(admin.ModelAdmin):
    list_display = ("webhook_id", "webhook_disabled", "updated_at")
    readonly_fields = ("webhook_id", "webhook_secret_encrypted", "updated_at")

    def has_add_permission(self, request):
        return not ProviderSettings.objects.exists()

    @admin.action(description="Register / reconcile Resend webhook")
    def register_webhook(self, request, queryset):
        ensure_webhook_registered()
        messages.success(request, "Webhook registration attempted.")

    actions = ["register_webhook"]
