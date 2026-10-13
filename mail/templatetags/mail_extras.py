from __future__ import annotations

from datetime import datetime
from email.utils import parseaddr

from django import template
from django.utils import timezone

register = template.Library()


@register.filter
def mail_list_date(value: datetime | None) -> str:
    """Gmail-style date: time if today, else month/day (and year if not current year)."""
    if value is None:
        return ""
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    local = timezone.localtime(value)
    now = timezone.localtime()
    if local.date() == now.date():
        hour = int(local.strftime("%I"))
        return f"{hour}:{local.strftime('%M')} {local.strftime('%p')}"
    if local.year == now.year:
        return f"{local.strftime('%b')} {local.day}"
    return f"{local.month}/{local.day}/{local.year}"


@register.filter
def message_sort_time(message, copy) -> datetime | None:
    return message.sent_at or copy.created_at


@register.filter
def mail_display_name(address: str) -> str:
    name, addr = parseaddr(address or "")
    if name:
        return name
    if addr:
        local = addr.split("@", 1)[0]
        return local or addr
    return "(unknown)"


@register.filter
def mail_address_only(address: str) -> str:
    _, addr = parseaddr(address or "")
    return addr or (address or "").strip()


@register.filter
def mail_avatar_initial(address: str) -> str:
    name, addr = parseaddr(address or "")
    label = name or (addr.split("@", 1)[0] if addr else "")
    label = (label or "?").strip()
    return label[0].upper()


@register.filter
def mail_message_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())
    local = timezone.localtime(value)
    hour = int(local.strftime("%I"))
    return f"{local.strftime('%a, %b')} {local.day}, {local.year} at {hour}:{local.strftime('%M %p')}"


@register.filter
def message_list_sender(message, folder: str) -> str:
    if folder == "sent":
        return (message.to_index or "").split(",")[0].strip() or "(no recipient)"
    return message.from_address or "(unknown)"


@register.simple_tag
def message_snippet(message, max_length: int = 96) -> str:
    body = (message.body_text_index or "").strip().replace("\n", " ")
    if len(body) <= max_length:
        return body
    return body[: max_length - 1].rstrip() + "…"
