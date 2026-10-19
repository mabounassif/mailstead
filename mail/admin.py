from django.contrib import admin

from mail.models import (
    Conversation,
    ConversationEvent,
    ConversationParticipant,
    FilterRule,
    Message,
    MessageAttachment,
    MessageCopy,
    OutboundMessage,
    UnroutedMessage,
    WebhookEvent,
)


class _ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(_ReadOnlyAdmin):
    list_display = ("topic", "mailbox", "topic_key", "created_at")
    search_fields = ("topic", "topic_key")


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(_ReadOnlyAdmin):
    list_display = ("conversation", "address", "kind", "active")
    list_filter = ("kind", "active")


@admin.register(ConversationEvent)
class ConversationEventAdmin(_ReadOnlyAdmin):
    list_display = ("conversation", "kind", "address", "created_at")
    list_filter = ("kind",)


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
