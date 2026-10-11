from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import include, path, reverse

from accounts.views import SetupView
from core.views import healthz, readyz
from provider.usage_views import usage_panel
from provider.webhooks import resend_webhook


def home(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect(reverse("mail_inbox"))
    return redirect(reverse("login"))


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),
    path("readyz", readyz),
    path("hooks/resend", resend_webhook),
    path("accounts/", include("accounts.urls")),
    path("mail/", include("mail.urls")),
    path("ops/", include("storage.urls")),
    path("ops/resend-usage/", usage_panel, name="usage_panel"),
    path("ops/enterprise/", include("enterprise.urls")),
    path("setup/<str:token>/", SetupView.as_view(), name="setup"),
    path("", home),
]
