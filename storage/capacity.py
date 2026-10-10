from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from core.paths import data_root


@dataclass
class CapacityInfo:
    label: str
    total_bytes: int
    used_bytes: int
    free_bytes: int


def _db_size() -> int:
    from django.db import connection

    if connection.vendor == "sqlite":
        p = connection.settings_dict.get("NAME")
        if p and Path(p).is_file():
            return Path(p).stat().st_size
    return 0


def physical_capacity() -> CapacityInfo:
    override = getattr(settings, "DATA_VOLUME_CAPACITY_BYTES", None)
    root = data_root()
    try:
        st = os.statvfs(root)
        total = st.f_blocks * st.f_frsize
        free = st.f_bavail * st.f_frsize
        used = total - free
        if override:
            return CapacityInfo("configured", int(override), used, max(0, int(override) - used))
        return CapacityInfo("measured", total, used, free)
    except OSError:
        if override:
            return CapacityInfo("configured", int(override), 0, int(override))
        return CapacityInfo("unknown", 0, 0, 0)


def email_budget_bytes() -> int:
    configured = getattr(settings, "EMAIL_BUDGET_BYTES", None)
    if configured:
        return int(configured)
    phys = physical_capacity()
    if phys.total_bytes:
        return int(phys.total_bytes * 0.7)
    return 1024 * 1024 * 1024


def disk_reserve_bytes() -> int:
    reserve = int(getattr(settings, "DISK_RESERVE_BYTES", 256 * 1024 * 1024))
    tmp_cap = int(getattr(settings, "TMP_CAP_BYTES", 64 * 1024 * 1024))
    return max(reserve, _db_size() * 2 + tmp_cap)


def effective_email_capacity(ledger) -> int:
    phys = physical_capacity()
    budget = email_budget_bytes()
    headroom = disk_reserve_bytes()
    by_budget = budget - ledger.email_consumed_bytes - ledger.reserved_bytes - ledger.overflow_bytes
    by_disk = phys.free_bytes - headroom
    return max(0, min(by_budget, by_disk))
