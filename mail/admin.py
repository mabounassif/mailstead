from django.contrib import admin

from mail.models import (
    FilterRule,
    Message,
    MessageAttachment,
    MessageCopy,
    OutboundMessage,
    UnroutedMessage,
    WebhookEvent,
)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "from_address", "resend_email_id", "archived", "unretrievable")
    search_fields = ("subject", "from_address", "resend_email_id")


@admin.register(MessageCopy)
class MessageCopyAdmin(admin.ModelAdmin):
    list_display = ("mailbox", "folder", "is_unread", "message")
    list_filter = ("folder",)


@admin.register(OutboundMessage)
class OutboundMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "mailbox", "state", "provider_id", "created_at")
    list_filter = ("state",)


@admin.register(UnroutedMessage)
class UnroutedMessageAdmin(admin.ModelAdmin):
    list_display = ("resend_email_id", "received_at")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("svix_id", "event_type", "received_at")


@admin.register(FilterRule)
class FilterRuleAdmin(admin.ModelAdmin):
    list_display = ("mailbox", "scope", "pattern", "action")


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ("message", "filename", "size_bytes")
