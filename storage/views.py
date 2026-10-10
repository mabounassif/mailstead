from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from jobs.models import Job, WorkerHeartbeat
from provider.models import ProviderSettings
from storage.capacity import effective_email_capacity, physical_capacity
from storage.models import MailboxStorage, OverflowItem, StorageLedger


@staff_member_required
def ops_dashboard(request):
    ledger = StorageLedger.objects.first() or StorageLedger.objects.create()
    phys = physical_capacity()
    return render(
        request,
        "storage/ops.html",
        {
            "ledger": ledger,
            "physical": phys,
            "effective_capacity": effective_email_capacity(ledger),
            "mailboxes": MailboxStorage.objects.select_related("mailbox").order_by("-charged_bytes")[:50],
            "overflow_count": OverflowItem.objects.count(),
            "dead_jobs": Job.objects.filter(state=Job.State.DEAD).count()[:20],
            "worker": WorkerHeartbeat.objects.order_by("-updated_at").first(),
            "webhook": ProviderSettings.objects.first(),
        },
    )
