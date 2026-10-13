from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render

from mail.models import Message
from provider.usage_service import latest_usage_display, refresh_usage


@staff_member_required
def usage_panel(request):
    if request.method == "POST":
        refresh_usage()
        return redirect("usage_panel")
    ctx = latest_usage_display()
    ctx["portal_message_count"] = Message.objects.count()
    ctx["active_nav"] = "ops"
    return render(request, "provider/usage.html", ctx)
