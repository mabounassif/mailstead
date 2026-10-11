from __future__ import annotations

from django.conf import settings

from jobs.worker_runtime import register
from mail.inbound import ingest_inbound
from mail.outbound import apply_outbound_status, send_outbound
from mail.reconcile import reconcile_received
from provider.webhook_register import ensure_webhook_registered


@register("inbound")
def handle_inbound(job):
    ingest_inbound(
        job.payload["email_id"],
        job.payload.get("webhook"),
        notify=job.payload.get("notify", True),
    )


@register("outbound_send")
def handle_outbound_send(job):
    send_outbound(job.payload["outbound_id"])


@register("outbound_status")
def handle_outbound_status(job):
    apply_outbound_status(job.payload)


@register("reconcile_received")
def handle_reconcile(_job):
    reconcile_received()


@register("register_webhook")
def handle_register_webhook(_job):
    if not settings.PUBLIC_URL:
        return
    ensure_webhook_registered()
