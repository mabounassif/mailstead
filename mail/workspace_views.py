from __future__ import annotations

import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from mail.models import AgentProfile, Card, MessageAttachment, Project, VaultEntry
from mail.views import _mailbox_or_notice
from provider.crypto import decrypt, encrypt
from storage.capacity import physical_capacity


def _format_bytes(size: int) -> str:
    value = float(max(size, 0))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{int(size)} B"


def _workspace_or_notice(request: HttpRequest):
    return _mailbox_or_notice(request)


@login_required
def drive(request: HttpRequest) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    capacity = physical_capacity()
    files = []
    attachments = (
        MessageAttachment.objects.filter(message__copies__mailbox=mailbox)
        .select_related("blob", "message")
        .order_by("-id")
        .distinct()
    )
    for attachment in attachments:
        path = attachment.blob.path if attachment.blob_id else ""
        local = bool(path and os.path.isfile(path))
        files.append(
            {
                "name": attachment.filename or "(unnamed file)",
                "size": _format_bytes(attachment.size_bytes or (attachment.blob.size_bytes if attachment.blob_id else 0)),
                "subject": attachment.message.subject or "(no subject)",
                "local": local,
            }
        )
    return render(
        request,
        "mail/drive.html",
        {
            "active_nav": "drive",
            "files": files,
            "disk_used": _format_bytes(capacity.used_bytes),
            "disk_total": _format_bytes(capacity.total_bytes),
            "disk_free": _format_bytes(capacity.free_bytes),
        },
    )


@login_required
def cards(request: HttpRequest) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        body = (request.POST.get("body") or "").strip()
        if not title:
            messages.error(request, "A card needs a title.")
        else:
            Card.objects.create(mailbox=mailbox, title=title[:160], body=body)
            return redirect("workspace_cards")
    return render(
        request,
        "mail/cards.html",
        {"active_nav": "cards", "cards": Card.objects.filter(mailbox=mailbox)},
    )


@login_required
@require_POST
def delete_card(request: HttpRequest, card_id: int) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    card = get_object_or_404(Card, pk=card_id, mailbox=mailbox)
    card.delete()
    return redirect("workspace_cards")


@login_required
def passwords(request: HttpRequest) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    if request.method == "POST":
        label = (request.POST.get("label") or "").strip()
        username = (request.POST.get("username") or "").strip()
        secret = request.POST.get("secret") or ""
        if not label or not secret:
            messages.error(request, "A password needs a name and a secret.")
        else:
            VaultEntry.objects.create(
                mailbox=mailbox,
                label=label[:160],
                username=username[:320],
                secret=encrypt(secret),
            )
            return redirect("workspace_passwords")
    show = request.GET.get("show") or ""
    entries = []
    for entry in VaultEntry.objects.filter(mailbox=mailbox):
        opened = str(entry.id) == show
        revealed = ""
        if opened:
            try:
                revealed = decrypt(entry.secret)
            except Exception:
                revealed = ""
        entries.append(
            {
                "id": entry.id,
                "label": entry.label,
                "username": entry.username,
                "secret": revealed,
                "open": opened,
            }
        )
    return render(
        request,
        "mail/passwords.html",
        {"active_nav": "passwords", "entries": entries},
    )


@login_required
@require_POST
def delete_password(request: HttpRequest, entry_id: int) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    entry = get_object_or_404(VaultEntry, pk=entry_id, mailbox=mailbox)
    entry.delete()
    return redirect("workspace_passwords")


@login_required
def agents(request: HttpRequest) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        instructions = (request.POST.get("instructions") or "").strip()
        if not name:
            messages.error(request, "An agent needs a name.")
        else:
            AgentProfile.objects.create(mailbox=mailbox, name=name[:80], instructions=instructions)
            return redirect("workspace_agents")
    return render(
        request,
        "mail/agents.html",
        {"active_nav": "agents", "agents": AgentProfile.objects.filter(mailbox=mailbox)},
    )


@login_required
@require_POST
def delete_agent(request: HttpRequest, agent_id: int) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    agent = get_object_or_404(AgentProfile, pk=agent_id, mailbox=mailbox)
    agent.delete()
    return redirect("workspace_agents")


@login_required
@require_POST
def create_project(request: HttpRequest) -> HttpResponse:
    mailbox, notice = _workspace_or_notice(request)
    if notice is not None:
        return notice
    name = (request.POST.get("name") or "").strip()
    if not name:
        messages.error(request, "A project needs a name.")
        return redirect("mail_inbox")
    try:
        project = Project.objects.create(mailbox=mailbox, name=name[:80])
    except IntegrityError:
        messages.error(request, "That project already exists.")
        return redirect("mail_inbox")
    return redirect(f"{reverse('mail_inbox')}?project={project.id}")
