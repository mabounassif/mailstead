from __future__ import annotations

import time

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from jobs.queue import enqueue


def _debounce_seconds() -> int:
    return int(getattr(settings, "PUSH_DEBOUNCE_SECONDS", 45))


def _cache_key(mailbox_id: int) -> str:
    return f"mailstead:push:pending:{mailbox_id}"


def schedule_new_mail_push(mailbox_id: int, copy_id: int) -> None:
    key = _cache_key(mailbox_id)
    pending = cache.get(key) or {"copy_ids": []}
    copy_ids = pending.get("copy_ids") or []
    if copy_id not in copy_ids:
        copy_ids.append(copy_id)
    cache.set(key, {"copy_ids": copy_ids}, timeout=3600)

    bucket = int(time.time()) // _debounce_seconds()
    dedupe = f"push:mb:{mailbox_id}:{bucket}"
    run_after = timezone.now() + timezone.timedelta(seconds=_debounce_seconds())
    enqueue(
        "push_notify_mailbox",
        {"mailbox_id": mailbox_id},
        dedupe_key=dedupe,
        run_after=run_after,
    )


def pop_pending_copy_ids(mailbox_id: int) -> list[int]:
    key = _cache_key(mailbox_id)
    pending = cache.get(key) or {}
    copy_ids = list(pending.get("copy_ids") or [])
    cache.delete(key)
    return copy_ids
