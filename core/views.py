from django.http import HttpRequest, HttpResponse, JsonResponse

from core.health import liveness, readiness


def healthz(_request: HttpRequest) -> JsonResponse:
    return JsonResponse(liveness())


def readyz(_request: HttpRequest) -> HttpResponse:
    ok, body = readiness()
    return JsonResponse(body, status=200 if ok else 503)
