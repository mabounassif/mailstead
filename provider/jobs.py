from django.conf import settings

from jobs.worker_runtime import register
from provider.usage_service import refresh_usage


@register("noop")
def _noop(_job):
    return


@register("usage_refresh")
def handle_usage_refresh(_job):
    refresh_usage()
