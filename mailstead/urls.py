from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.urls import include, path

from accounts.views import SetupView
from core.views import healthz, readyz


def home(_request: HttpRequest) -> HttpResponse:
    return HttpResponse("Mailstead", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz),
    path("readyz", readyz),
    path("accounts/", include("accounts.urls")),
    path("setup/<str:token>/", SetupView.as_view(), name="setup"),
    path("", home),
]
