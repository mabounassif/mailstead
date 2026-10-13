from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from jobs.models import Job, WorkerHeartbeat
from provider.models import ProviderSettings
from storage.capacity import disk_reserve_bytes, effective_email_capacity, email_budget_bytes, physical_capacity
from storage.models import OverflowItem, StorageLedger
from storage.ops_display import mailbox_usage_rows, physical_source_label, webhook_summary, worker_health


@staff_member_required
def ops_dashboard(request):
    ledger = StorageLedger.objects.first() or StorageLedger.objects.create()
    phys = physical_capacity()
    budget = email_budget_bytes()
    consumed = ledger.email_consumed_bytes
    reserved = ledger.reserved_bytes
    overflow = ledger.overflow_bytes
    budget_used = consumed + reserved + overflow
    disk_pct = round(100 * phys.used_bytes / phys.total_bytes, 1) if phys.total_bytes else None
    budget_pct = round(100 * budget_used / budget, 1) if budget else None
    return render(
        request,
        "storage/ops.html",
        {
            "ledger": ledger,
            "physical": phys,
            "physical_source": physical_source_label(phys.label),
            "disk_used_percent": disk_pct,
            "email_budget_bytes": budget,
            "email_budget_used_bytes": budget_used,
            "email_budget_percent": budget_pct,
            "disk_reserve_bytes": disk_reserve_bytes(),
            "effective_capacity": effective_email_capacity(ledger),
            "mailbox_rows": mailbox_usage_rows(),
            "overflow_count": OverflowItem.objects.count(),
            "dead_jobs": Job.objects.filter(state=Job.State.DEAD).count(),
            "queued_jobs": Job.objects.filter(state=Job.State.QUEUED).count(),
            "running_jobs": Job.objects.filter(state=Job.State.RUNNING).count(),
            "worker": worker_health(WorkerHeartbeat.objects.order_by("-updated_at").first()),
            "webhook": webhook_summary(ProviderSettings.objects.first()),
            "active_nav": "ops",
        },
    )
