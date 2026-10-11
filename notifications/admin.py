from django.contrib import admin

from notifications.models import NotificationPreference, PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "endpoint_hash", "created_at", "revoked_at", "last_error")
    list_filter = ("revoked_at",)
    search_fields = ("user__username", "endpoint")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "enabled", "new_mail", "preview_mode", "updated_at")
