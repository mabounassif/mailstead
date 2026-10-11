from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest


def _parse_rate(limit: str) -> tuple[int, int]:
    """Parse '5/h' -> (5, 3600)."""
    count_part, window_part = limit.split("/")
    count = int(count_part)
    window = {"s": 1, "m": 60, "h": 3600, "d": 86400}[window_part[0]]
    return count, window


def password_reset_throttled(request: HttpRequest) -> bool:
    limit = settings.PASSWORD_RESET_RATE_LIMIT
    count, window = _parse_rate(limit)
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"pwd_reset_throttle:{ip}"
    current = cache.get(key, 0)
    return current >= count


def password_reset_hit(request: HttpRequest) -> None:
    limit = settings.PASSWORD_RESET_RATE_LIMIT
    count, window = _parse_rate(limit)
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"pwd_reset_throttle:{ip}"
    current = cache.get(key, 0)
    cache.set(key, current + 1, window)
