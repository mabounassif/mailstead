from __future__ import annotations

import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from notifications.models import NotificationPreference, PushSubscription
from notifications.push import endpoint_allowed, push_configured, push_keys_present
from notifications.services import prefs_for_user, send_test_notification


@require_GET
@cache_control(max_age=3600, public=True)
def web_manifest(request: HttpRequest) -> JsonResponse:
    base = settings.PUBLIC_URL.rstrip("/")
    return JsonResponse(
        {
            "name": "Mailstead",
            "short_name": "Mailstead",
            "id": base + "/",
            "start_url": base + "/mail/",
            "scope": base + "/",
            "display": "standalone",
            "background_color": "#2563eb",
            "theme_color": "#2563eb",
            "icons": [
                {
                    "src": base + "/static/mailstead/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
                {
                    "src": base + "/static/mailstead/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
                {
                    "src": base + "/static/mailstead/icon.svg",
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any",
                },
            ],
        }
    )


@require_GET
@cache_control(no_cache=True, must_revalidate=True)
def service_worker(request: HttpRequest) -> HttpResponse:
    js = """/* Mailstead push service worker — no HTML caching */
self.addEventListener("push", function (event) {
  var data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = {};
  }
  if (data.web_push === 8030 && data.notification) {
    return;
  }
  var n = data.notification || data;
  var title = n.title || "Mailstead";
  var options = {
    body: n.body || "",
    data: { navigate: n.navigate || n.data && n.data.navigate || "/" },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", function (event) {
  event.notification.close();
  var url = (event.notification.data && event.notification.data.navigate) || "/mail/";
  event.waitUntil(clients.openWindow(url));
});
"""
    return HttpResponse(js, content_type="application/javascript; charset=utf-8")


@login_required
@require_GET
def settings_page(request: HttpRequest) -> HttpResponse:
    pref = prefs_for_user(request.user)
    devices = PushSubscription.objects.filter(user=request.user, revoked_at__isnull=True).order_by("-created_at")
    return render(
        request,
        "notifications/settings.html",
        {
            "pref": pref,
            "preview_mode_choices": NotificationPreference.PreviewMode.choices,
            "devices": devices,
            "push_configured": push_configured(),
            "push_keys_invalid": push_keys_present() and not push_configured(),
            "vapid_public_key": settings.VAPID_PUBLIC_KEY,
            "active_nav": "notifications",
        },
    )


@login_required
@require_POST
def settings_save(request: HttpRequest) -> HttpResponse:
    pref = prefs_for_user(request.user)
    pref.enabled = request.POST.get("enabled") == "on"
    pref.new_mail = request.POST.get("new_mail") == "on"
    mode = request.POST.get("preview_mode", NotificationPreference.PreviewMode.PRIVATE)
    if mode in NotificationPreference.PreviewMode.values:
        pref.preview_mode = mode
    pref.save()
    return redirect("notifications_settings")


@login_required
@require_POST
def subscribe(request: HttpRequest) -> JsonResponse:
    if not push_configured():
        return JsonResponse({"ok": False, "error": "not_configured"}, status=503)
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)
    endpoint = body.get("endpoint") or ""
    keys = body.get("keys") or {}
    if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
        return JsonResponse({"ok": False, "error": "invalid_subscription"}, status=400)
    if not endpoint_allowed(endpoint):
        return JsonResponse({"ok": False, "error": "endpoint_not_allowed"}, status=400)

    endpoint_hash = PushSubscription.hash_endpoint(endpoint)
    label = (body.get("label") or "")[:64]
    ua = (request.META.get("HTTP_USER_AGENT") or "")[:255]
    sub, created = PushSubscription.objects.update_or_create(
        endpoint_hash=endpoint_hash,
        defaults={
            "user": request.user,
            "endpoint": endpoint,
            "keys_json": keys,
            "user_agent": ua,
            "label": label,
            "revoked_at": None,
            "last_error": "",
        },
    )
    return JsonResponse({"ok": True, "id": sub.pk, "created": created})


@login_required
@require_http_methods(["POST"])
def unsubscribe(request: HttpRequest) -> JsonResponse:
    try:
        body = json.loads(request.body.decode("utf-8") if request.body else "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        body = {}
    endpoint = body.get("endpoint") or request.POST.get("endpoint") or ""
    sub_id = body.get("id") or request.POST.get("id")
    qs = PushSubscription.objects.filter(user=request.user, revoked_at__isnull=True)
    if sub_id:
        qs = qs.filter(pk=sub_id)
    elif endpoint:
        qs = qs.filter(endpoint_hash=PushSubscription.hash_endpoint(endpoint))
    else:
        return JsonResponse({"ok": False, "error": "missing_target"}, status=400)
    updated = qs.update(revoked_at=timezone_now())
    return JsonResponse({"ok": True, "removed": updated})


def timezone_now():
    from django.utils import timezone

    return timezone.now()


@login_required
@require_POST
def test_push(request: HttpRequest) -> HttpResponse:
    if not push_configured():
        return redirect("notifications_settings")
    send_test_notification(request.user)
    return redirect("notifications_settings")


@login_required
@require_POST
def remove_device(request: HttpRequest, device_id: int) -> HttpResponse:
    PushSubscription.objects.filter(user=request.user, pk=device_id).update(revoked_at=timezone_now())
    return redirect("notifications_settings")
