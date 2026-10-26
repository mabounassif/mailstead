from __future__ import annotations

import json
from collections.abc import Callable

from django.http import Http404, HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.models import Mailbox
from api.auth import user_from_bearer


class ApiError(Exception):
    def __init__(self, status: int, code: str, detail: str = "", fields: dict | None = None):
        super().__init__(detail or code)
        self.status = status
        self.code = code
        self.detail = detail
        self.fields = fields


def json_ok(data: dict, status: int = 200) -> JsonResponse:
    return JsonResponse(data, status=status)


def json_error(status: int, code: str, detail: str = "", fields: dict | None = None) -> JsonResponse:
    body: dict = {"error": code}
    if detail:
        body["detail"] = detail
    if fields:
        body["fields"] = fields
    return JsonResponse(body, status=status)


def json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ApiError(400, "invalid_json")
    if not isinstance(data, dict):
        raise ApiError(400, "invalid_json")
    return data


def as_str(data: dict, key: str, default: str = "") -> str:
    if key not in data:
        return default
    value = data[key]
    if value is None:
        return default
    if not isinstance(value, str):
        raise ApiError(400, "invalid", fields={key: ["Must be a string."]})
    return value


def as_bool(data: dict, key: str) -> bool | None:
    if key not in data:
        return None
    value = data[key]
    if not isinstance(value, bool):
        raise ApiError(400, "invalid", fields={key: ["Must be true or false."]})
    return value


def as_str_list(data: dict, key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ApiError(400, "invalid", fields={key: ["Must be a list of strings."]})
    return [item.strip() for item in value if item.strip()]


def load_mailbox(request: HttpRequest, *, allow_disabled: bool = False):
    try:
        mailbox = request.user.mailbox
    except Mailbox.DoesNotExist:
        return None, json_error(409, "no_mailbox", "This account has no mailbox.")
    if mailbox.state == Mailbox.State.DISABLED and not allow_disabled:
        return None, json_error(403, "mailbox_disabled", "This account has been disabled.")
    return mailbox, None


def api_endpoint(methods: list[str], *, auth: bool = True, mailbox: bool = False) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @csrf_exempt
        @require_http_methods(methods)
        def wrapper(request: HttpRequest, *args, **kwargs):
            try:
                if auth:
                    user = user_from_bearer(request)
                    if user is None or not user.is_active:
                        return json_error(401, "unauthorized")
                    request.user = user
                if mailbox:
                    owned, error = load_mailbox(request)
                    if error is not None:
                        return error
                    kwargs["mailbox"] = owned
                return fn(request, *args, **kwargs)
            except ApiError as exc:
                return json_error(exc.status, exc.code, exc.detail, exc.fields)
            except Http404:
                return json_error(404, "not_found")
            except LookupError:
                return json_error(404, "not_found")
            except ValueError as exc:
                return json_error(400, "invalid", str(exc))

        return wrapper

    return decorator
