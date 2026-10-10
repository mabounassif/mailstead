from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import Alias, BootstrapState, Mailbox, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Recovery", {"fields": ("recovery_email",)}),
    )
    list_display = ("username", "recovery_email", "is_staff", "is_active")
    search_fields = ("username", "recovery_email")


@admin.register(Mailbox)
class MailboxAdmin(admin.ModelAdmin):
    list_display = ("address", "user", "quota_bytes", "over_quota", "state")
    list_filter = ("state", "over_quota")
    search_fields = ("address", "user__username")
    raw_id_fields = ("user",)


@admin.register(Alias)
class AliasAdmin(admin.ModelAdmin):
    list_display = ("address", "mailbox", "is_active")
    search_fields = ("address",)
    raw_id_fields = ("mailbox",)


@admin.register(BootstrapState)
class BootstrapStateAdmin(admin.ModelAdmin):
    list_display = ("id", "consumed_at", "consumed_by", "created_at")
    readonly_fields = ("token_hash", "consumed_at", "consumed_by", "created_at")
