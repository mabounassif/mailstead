from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render

from enterprise.client import activate, refresh_entitlements
from enterprise.entitlements import licensed_capability
from enterprise.models import EntitlementCache, License


@staff_member_required
def enterprise_page(request):
    lic = License.objects.first()
    cache = EntitlementCache.objects.first()
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "activate":
            activate(request.POST.get("license_key", ""))
            messages.success(request, "License activated.")
        elif action == "refresh":
            refresh_entitlements()
            messages.success(request, "Entitlements refreshed.")
        elif action == "configure":
            if lic:
                lic.configured = True
                lic.data_flow_accepted = request.POST.get("accept") == "1"
                lic.save()
        return redirect("enterprise_page")
    return render(
        request,
        "enterprise/page.html",
        {
            "license": lic,
            "cache": cache,
            "spam_licensed": licensed_capability("spam_filtering"),
        },
    )
