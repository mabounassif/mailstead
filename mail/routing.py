from __future__ import annotations

from accounts.models import Alias, Mailbox


def local_addresses() -> dict[str, Mailbox]:
    mapping: dict[str, Mailbox] = {}
    for mb in Mailbox.objects.filter(state=Mailbox.State.ACTIVE):
        mapping[mb.address.lower()] = mb
    for alias in Alias.objects.filter(is_active=True).select_related("mailbox"):
        if alias.mailbox.state == Mailbox.State.ACTIVE:
            mapping[alias.address.lower()] = alias.mailbox
    return mapping


def resolve_recipients(metadata: dict) -> list[Mailbox]:
    fields = metadata.get("to", []) + metadata.get("cc", []) + metadata.get("bcc", [])
    received_for = metadata.get("received_for") or metadata.get("for")
    if received_for:
        if isinstance(received_for, str):
            fields.append(received_for)
        else:
            fields.extend(received_for)
    local = local_addresses()
    seen = set()
    result: list[Mailbox] = []
    for raw in fields:
        addr = _bare_email(raw).lower()
        if not addr or addr in seen:
            continue
        seen.add(addr)
        mb = local.get(addr)
        if mb:
            result.append(mb)
    return result


def _bare_email(value) -> str:
    if isinstance(value, dict):
        return value.get("email") or value.get("address") or ""
    s = str(value)
    if "<" in s and ">" in s:
        return s.split("<", 1)[1].split(">", 1)[0].strip()
    return s.strip()
