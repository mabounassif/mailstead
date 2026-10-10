from __future__ import annotations

from mail.models import FilterRule, Folder


def folder_for_inbound(mailbox, meta: dict) -> str:
    from_addr = (meta.get("from") or "").lower()
    domain = from_addr.split("@")[-1] if "@" in from_addr else ""
    from django.db.models import Q

    rules = FilterRule.objects.filter(Q(mailbox=mailbox) | Q(mailbox__isnull=True))
    for rule in rules.order_by("-id"):
        target = from_addr if rule.scope == FilterRule.Scope.SENDER else domain
        if target and rule.pattern.lower() in target:
            if rule.action == FilterRule.Action.BLOCK:
                return Folder.JUNK
            return Folder.INBOX
    auth = meta.get("authentication") or {}
    if auth.get("dmarc") == "fail":
        return Folder.JUNK
    return Folder.INBOX
