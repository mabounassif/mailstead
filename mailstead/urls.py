from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import include, path

from accounts.views import SetupView
from core.views import healthz, readyz
from provider.webhooks import resend_webhook


def home(_request: HttpRequest) -> HttpResponse:
    return HttpResponse("Mailstead", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),
    path("readyz", readyz),
    path("hooks/resend", resend_webhook),
    path("accounts/", include("accounts.urls")),
    path("mail/", include("mail.urls")),
    path("setup/<str:token>/", SetupView.as_view(), name="setup"),
    path("", home),
]
