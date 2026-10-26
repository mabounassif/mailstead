from __future__ import annotations

import re

from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.http import FileResponse, HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.forms import RecoveryPasswordResetForm
from accounts.models import Mailbox
from accounts.password_reset import confirm_password_reset, send_password_reset
from accounts.throttles import password_reset_hit, password_reset_throttled
from api.auth import issue_token, revoke_token
from api.http import ApiError, api_endpoint, as_bool, as_str, as_str_list, json_body, json_error, json_ok
from api.reading import (
    chats_payload,
    contacts_payload,
    drive_payload,
    folder_queryset,
    message_detail_payload,
    page_payload,
    resolve_chat,
    search_queryset,
    serialize_chat,
)
from api.sending import reply_to_copy, send_chat, send_to_conversation, start_conversation
from axes.handlers.proxy import AxesProxyHandler
from axes.helpers import get_credentials
from mail.deletion import empty_trash, move_to_trash, purge_message_copy, restore_from_trash
from mail.models import Card, Conversation, Folder, MessageAttachment, MessageCopy, Project, VaultEntry
from notifications.models import NativePushDevice, NotificationPreference, PushSubscription
from notifications.services import prefs_for_user, send_test_notification, unread_inbox_count
from notifications.expo import expo_push_configured, register_expo_token
from provider.crypto import decrypt, encrypt

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _owned_copy(mailbox, copy_id: int) -> MessageCopy:
    return get_object_or_404(MessageCopy.objects.select_related("message"), pk=copy_id, mailbox=mailbox)


def _form_fields(form) -> dict:
    fields = {}
    for key, errors in form.errors.items():
        name = {"new_password1": "password", "new_password2": "password_confirm"}.get(key, key)
        fields[name] = [str(item) for item in errors]
    return fields


def _int_arg(value: str, name: str) -> int | None:
    if not value:
        return None
    if not value.isdigit():
        raise ApiError(400, "invalid", fields={name: ["Must be an id."]})
    return int(value)


@api_endpoint(["POST"], auth=False)
def login(request: HttpRequest):
    data = json_body(request)
    username = as_str(data, "username").strip()
    password = as_str(data, "password")
    if not username or not password:
        raise ApiError(400, "invalid", fields={"username": ["Username and password are required."]})
    credentials = get_credentials(username=username)
    if AxesProxyHandler.is_locked(request, credentials):
        return json_error(429, "locked", "Too many sign-in attempts. Try again later.")
    user = authenticate(request, username=username, password=password)
    if user is None:
        if AxesProxyHandler.is_locked(request, credentials):
            return json_error(429, "locked", "Too many sign-in attempts. Try again later.")
        return json_error(401, "invalid_credentials", "Unknown username or password.")
    try:
        mailbox = user.mailbox
    except Mailbox.DoesNotExist:
        mailbox = None
    if mailbox is not None and mailbox.state == Mailbox.State.DISABLED:
        return json_error(403, "mailbox_disabled", "This account has been disabled.")
    token = issue_token(user, label=as_str(data, "label")[:64])
    return json_ok(
        {
            "token": token,
            "username": user.get_username(),
            "mailbox": None
            if mailbox is None
            else {"address": mailbox.address, "state": mailbox.state},
        }
    )


@api_endpoint(["POST"])
def logout(request: HttpRequest):
    header = request.META.get("HTTP_AUTHORIZATION", "")
    raw = header[7:].strip() if header.startswith("Bearer ") else ""
    if raw:
        revoke_token(raw)
    return json_ok({"ok": True})


@api_endpoint(["POST"], auth=False)
def password_reset(request: HttpRequest):
    if password_reset_throttled(request):
        return json_error(429, "throttled", "Too many reset requests. Try again later.")
    data = json_body(request)
    form = RecoveryPasswordResetForm(data={"username": as_str(data, "username").strip()})
    if not form.is_valid():
        return json_error(400, "invalid", fields=_form_fields(form))
    password_reset_hit(request)
    send_password_reset(form.user)
    return json_ok({"ok": True})


@api_endpoint(["POST"], auth=False)
def password_reset_confirm(request: HttpRequest):
    data = json_body(request)
    try:
        result = confirm_password_reset(
            uidb64=as_str(data, "uid").strip(),
            token=as_str(data, "token").strip(),
            password=as_str(data, "password"),
            password_confirm=as_str(data, "password_confirm"),
        )
    except ValueError:
        return json_error(400, "invalid_token", "This reset link is invalid or expired.")
    from django.contrib.auth.models import AbstractBaseUser

    if isinstance(result, AbstractBaseUser):
        return json_ok({"ok": True})
    return json_error(400, "invalid", fields=_form_fields(result))


@api_endpoint(["GET"])
def me(request: HttpRequest):
    try:
        mailbox = request.user.mailbox
    except Mailbox.DoesNotExist:
        mailbox = None
    unread = unread_inbox_count(mailbox) if mailbox is not None and mailbox.state == Mailbox.State.ACTIVE else 0
    return json_ok(
        {
            "username": request.user.get_username(),
            "mailbox": None
            if mailbox is None
            else {"address": mailbox.address, "state": mailbox.state},
            "unread_count": unread,
        }
    )


@api_endpoint(["GET"], mailbox=True)
def chats(request: HttpRequest, mailbox):
    return json_ok(chats_payload(mailbox))


def _opened_from_request(mailbox, data_or_query, *, from_body: bool):
    if from_body:
        project_id = data_or_query.get("project_id")
        channel_id = data_or_query.get("channel_id")
        if project_id is not None and not isinstance(project_id, int):
            raise ApiError(400, "invalid", fields={"project_id": ["Must be an id."]})
        if channel_id is not None and not isinstance(channel_id, int):
            raise ApiError(400, "invalid", fields={"channel_id": ["Must be an id."]})
        dm = as_str(data_or_query, "dm")
        contact = as_str(data_or_query, "contact")
    else:
        project_id = _int_arg(data_or_query.get("project") or "", "project")
        channel_id = _int_arg(data_or_query.get("channel") or "", "channel")
        dm = (data_or_query.get("dm") or "").strip()
        contact = (data_or_query.get("contact") or "").strip()
    return resolve_chat(mailbox, dm=dm, project_id=project_id, contact=contact, channel_id=channel_id)


@api_endpoint(["GET", "POST"], mailbox=True)
def conversations(request: HttpRequest, mailbox):
    if request.method == "GET":
        opened = _opened_from_request(mailbox, request.GET, from_body=False)
        return json_ok(serialize_chat(mailbox, opened))
    data = json_body(request)
    if "to" in data:
        result = start_conversation(
            mailbox,
            as_str_list(data, "to"),
            as_str(data, "subject"),
            as_str(data, "body"),
            add=as_str(data, "add"),
        )
        return json_ok(result, status=201)
    opened = _opened_from_request(mailbox, data, from_body=True)
    if opened.conversation is not None and not opened.project:
        result = send_to_conversation(
            mailbox,
            opened.conversation,
            as_str(data, "body"),
            subject=as_str(data, "subject"),
            add=as_str(data, "add"),
            drop=as_str(data, "drop"),
        )
        return json_ok(result, status=201)
    result = send_chat(
        mailbox,
        mode="group" if opened.mode == "group" else "contact",
        chats=opened.chats,
        contact_address=opened.contact_address,
        project=opened.project,
        thread=opened.thread,
        body=as_str(data, "body"),
        subject=as_str(data, "subject") or (opened.conversation.topic if opened.conversation else opened.label),
        add=as_str(data, "add"),
        drop=as_str(data, "drop"),
    )
    return json_ok(result, status=201)


@api_endpoint(["GET", "POST"], mailbox=True)
def conversation_messages(request: HttpRequest, mailbox, conversation_id: int):
    conversation = get_object_or_404(Conversation, pk=conversation_id, mailbox=mailbox)
    if request.method == "GET":
        opened = resolve_chat(mailbox, channel_id=conversation.id)
        return json_ok(serialize_chat(mailbox, opened))
    data = json_body(request)
    result = send_to_conversation(
        mailbox,
        conversation,
        as_str(data, "body"),
        subject=as_str(data, "subject"),
        add=as_str(data, "add"),
        drop=as_str(data, "drop"),
    )
    return json_ok(result, status=201)


@api_endpoint(["GET"], mailbox=True)
def message_detail(request: HttpRequest, mailbox, copy_id: int):
    copy = _owned_copy(mailbox, copy_id)
    load_images = request.GET.get("load_images") == "1"
    return json_ok(message_detail_payload(copy, mailbox, load_images=load_images))


@api_endpoint(["POST"], mailbox=True)
def message_junk(request: HttpRequest, mailbox, copy_id: int):
    copy = _owned_copy(mailbox, copy_id)
    copy.folder = Folder.JUNK
    copy.save(update_fields=["folder"])
    return json_ok({"ok": True, "folder": copy.folder})


@api_endpoint(["POST"], mailbox=True)
def message_not_junk(request: HttpRequest, mailbox, copy_id: int):
    copy = _owned_copy(mailbox, copy_id)
    copy.folder = Folder.INBOX
    copy.save(update_fields=["folder"])
    return json_ok({"ok": True, "folder": copy.folder})


@api_endpoint(["POST"], mailbox=True)
def message_trash(request: HttpRequest, mailbox, copy_id: int):
    copy = _owned_copy(mailbox, copy_id)
    message_id = copy.message_id
    move_to_trash(copy)
    remaining = MessageCopy.objects.filter(pk=copy_id, mailbox=mailbox).first()
    if remaining is None:
        remaining = MessageCopy.objects.filter(message_id=message_id, mailbox=mailbox, folder=Folder.TRASH).first()
    return json_ok(
        {
            "ok": True,
            "folder": Folder.TRASH,
            "copy_id": remaining.id if remaining is not None else None,
        }
    )


@api_endpoint(["POST"], mailbox=True)
def message_restore(request: HttpRequest, mailbox, copy_id: int):
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox, folder=Folder.TRASH)
    restore_from_trash(copy)
    return json_ok({"ok": True, "folder": Folder.INBOX})


@api_endpoint(["POST"], mailbox=True)
def message_purge(request: HttpRequest, mailbox, copy_id: int):
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox, folder=Folder.TRASH)
    purge_message_copy(copy)
    return json_ok({"ok": True})


@api_endpoint(["POST"], mailbox=True)
def message_reply(request: HttpRequest, mailbox, copy_id: int):
    copy = _owned_copy(mailbox, copy_id)
    data = json_body(request)
    return json_ok(reply_to_copy(mailbox, copy, as_str(data, "body"), reply_all=False), status=201)


@api_endpoint(["POST"], mailbox=True)
def message_reply_all(request: HttpRequest, mailbox, copy_id: int):
    copy = _owned_copy(mailbox, copy_id)
    data = json_body(request)
    return json_ok(reply_to_copy(mailbox, copy, as_str(data, "body"), reply_all=True), status=201)


@api_endpoint(["GET"], mailbox=True)
def message_eml(request: HttpRequest, mailbox, copy_id: int):
    copy = _owned_copy(mailbox, copy_id)
    message = copy.message
    if not message.blob_id:
        raise ApiError(404, "not_found")
    return FileResponse(open(message.blob.path, "rb"), as_attachment=True, filename="message.eml")


@api_endpoint(["GET"], mailbox=True)
def message_attachment(request: HttpRequest, mailbox, copy_id: int, attachment_id: int):
    copy = _owned_copy(mailbox, copy_id)
    attachment = get_object_or_404(MessageAttachment, pk=attachment_id, message=copy.message)
    if not attachment.blob_id or not SHA256_RE.match(attachment.blob.sha256):
        raise ApiError(404, "not_found")
    filename = (attachment.filename or "attachment").replace("\r", "").replace("\n", "")
    return FileResponse(open(attachment.blob.path, "rb"), as_attachment=True, filename=filename)


@api_endpoint(["GET"], mailbox=True)
def folder(request: HttpRequest, mailbox, folder: str):
    qs = folder_queryset(mailbox, folder)
    return json_ok(page_payload(qs, request.GET.get("page") or "1"))


@api_endpoint(["POST"], mailbox=True)
def trash_empty(request: HttpRequest, mailbox):
    return json_ok({"ok": True, "deleted": empty_trash(mailbox)})


@api_endpoint(["GET"], mailbox=True)
def search(request: HttpRequest, mailbox):
    query = (request.GET.get("q") or "").strip()
    return json_ok({"q": query, **page_payload(search_queryset(mailbox, query), request.GET.get("page") or "1")})


@api_endpoint(["GET"], mailbox=True)
def drive(request: HttpRequest, mailbox):
    return json_ok(drive_payload(mailbox))


@api_endpoint(["GET"], mailbox=True)
def contacts(request: HttpRequest, mailbox):
    return json_ok(contacts_payload(mailbox))


@api_endpoint(["POST"], mailbox=True)
def projects(request: HttpRequest, mailbox):
    data = json_body(request)
    name = as_str(data, "name").strip()
    if not name:
        raise ApiError(400, "invalid", "A project needs a name.", {"name": ["A project needs a name."]})
    try:
        project = Project.objects.create(mailbox=mailbox, name=name[:80])
    except IntegrityError:
        raise ApiError(400, "invalid", "That project already exists.", {"name": ["That project already exists."]})
    return json_ok({"id": project.id, "name": project.name}, status=201)


def _card_payload(card: Card) -> dict:
    return {"id": card.id, "title": card.title, "body": card.body, "updated_at": card.updated_at.isoformat()}


@api_endpoint(["GET", "POST"], mailbox=True)
def cards(request: HttpRequest, mailbox):
    if request.method == "GET":
        return json_ok({"cards": [_card_payload(card) for card in Card.objects.filter(mailbox=mailbox)]})
    data = json_body(request)
    title = as_str(data, "title").strip()
    if not title:
        raise ApiError(400, "invalid", "A card needs a title.", {"title": ["A card needs a title."]})
    card = Card.objects.create(mailbox=mailbox, title=title[:160], body=as_str(data, "body").strip())
    return json_ok(_card_payload(card), status=201)


@api_endpoint(["DELETE"], mailbox=True)
def card_delete(request: HttpRequest, mailbox, card_id: int):
    card = get_object_or_404(Card, pk=card_id, mailbox=mailbox)
    card.delete()
    return json_ok({"ok": True})


def _vault_payload(entry: VaultEntry) -> dict:
    return {"id": entry.id, "label": entry.label, "username": entry.username}


@api_endpoint(["GET", "POST"], mailbox=True)
def vault(request: HttpRequest, mailbox):
    if request.method == "GET":
        return json_ok({"entries": [_vault_payload(entry) for entry in VaultEntry.objects.filter(mailbox=mailbox)]})
    data = json_body(request)
    label = as_str(data, "label").strip()
    secret = as_str(data, "secret")
    if not label or not secret:
        raise ApiError(400, "invalid", "A password needs a name and a secret.")
    entry = VaultEntry.objects.create(
        mailbox=mailbox,
        label=label[:160],
        username=as_str(data, "username").strip()[:320],
        secret=encrypt(secret),
    )
    return json_ok(_vault_payload(entry), status=201)


@api_endpoint(["DELETE"], mailbox=True)
def vault_delete(request: HttpRequest, mailbox, entry_id: int):
    entry = get_object_or_404(VaultEntry, pk=entry_id, mailbox=mailbox)
    entry.delete()
    return json_ok({"ok": True})


@api_endpoint(["POST"], mailbox=True)
def vault_reveal(request: HttpRequest, mailbox, entry_id: int):
    entry = get_object_or_404(VaultEntry, pk=entry_id, mailbox=mailbox)
    try:
        secret = decrypt(entry.secret)
    except Exception:
        secret = ""
    return json_ok({"id": entry.id, "secret": secret})


def _preference_payload(user) -> dict:
    pref = prefs_for_user(user)
    from notifications.push import push_configured

    return {
        "enabled": pref.enabled,
        "new_mail": pref.new_mail,
        "preview_mode": pref.preview_mode,
        "preview_modes": [value for value, _label in NotificationPreference.PreviewMode.choices],
        "push_configured": push_configured(),
        "expo_push_configured": expo_push_configured(),
    }


def _device_rows(user) -> list[dict]:
    rows = []
    web = PushSubscription.objects.filter(user=user, revoked_at__isnull=True).order_by("-created_at")
    for device in web:
        rows.append(
            {
                "id": device.id,
                "kind": "web",
                "label": device.label or "Web browser",
                "created_at": device.created_at.isoformat(),
            }
        )
    native = NativePushDevice.objects.filter(user=user, revoked_at__isnull=True).order_by("-created_at")
    for device in native:
        rows.append(
            {
                "id": device.id,
                "kind": "expo",
                "label": device.label or "Mailstead app",
                "created_at": device.created_at.isoformat(),
            }
        )
    return rows


@api_endpoint(["GET", "PATCH"])
def notification_preferences(request: HttpRequest):
    if request.method == "GET":
        return json_ok(_preference_payload(request.user))
    data = json_body(request)
    pref = prefs_for_user(request.user)
    enabled = as_bool(data, "enabled")
    new_mail = as_bool(data, "new_mail")
    if enabled is not None:
        pref.enabled = enabled
    if new_mail is not None:
        pref.new_mail = new_mail
    if "preview_mode" in data:
        mode = as_str(data, "preview_mode")
        if mode not in NotificationPreference.PreviewMode.values:
            raise ApiError(400, "invalid", fields={"preview_mode": ["Choose a preview mode."]})
        pref.preview_mode = mode
    pref.save()
    return json_ok(_preference_payload(request.user))


@api_endpoint(["GET"])
def notification_devices(request: HttpRequest):
    return json_ok({"devices": _device_rows(request.user)})


@api_endpoint(["DELETE"])
def notification_device_remove(request: HttpRequest, device_id: int):
    kind = (request.GET.get("kind") or "").strip()
    now = timezone.now()
    if kind == "web":
        updated = PushSubscription.objects.filter(user=request.user, pk=device_id, revoked_at__isnull=True).update(
            revoked_at=now
        )
    elif kind == "expo":
        updated = NativePushDevice.objects.filter(user=request.user, pk=device_id, revoked_at__isnull=True).update(
            revoked_at=now
        )
    else:
        raise ApiError(400, "invalid", fields={"kind": ["Use web or expo."]})
    if not updated:
        raise ApiError(404, "not_found")
    return json_ok({"ok": True})


@api_endpoint(["POST"])
def notification_test(request: HttpRequest):
    from notifications.push import push_configured

    if not push_configured() and not expo_push_configured():
        return json_error(503, "not_configured", "Push is not configured on this server.")
    sent = send_test_notification(request.user)
    return json_ok({"ok": True, "sent": sent})


@api_endpoint(["POST"])
def notification_expo(request: HttpRequest):
    data = json_body(request)
    device = register_expo_token(request.user, as_str(data, "token").strip(), label=as_str(data, "label").strip())
    return json_ok({"ok": True, "id": device.id}, status=201)
