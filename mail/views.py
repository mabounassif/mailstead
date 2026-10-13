from __future__ import annotations

import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from django.views.decorators.http import require_POST

from mail.compose import reply_all_recipients, send_compose
from mail.deletion import empty_trash, move_to_trash, purge_message_copy, restore_from_trash
from mail.html_safety import sanitize_html
from accounts.models import Mailbox
from mail.models import Folder, MessageAttachment, MessageCopy

SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _mailbox_or_notice(request: HttpRequest) -> tuple[Mailbox | None, HttpResponse | None]:
    try:
        return request.user.mailbox, None
    except Mailbox.DoesNotExist:
        return None, render(
            request,
            "mail/no_mailbox.html",
            {"is_staff": request.user.is_staff},
        )


def _mailbox(request: HttpRequest) -> Mailbox:
    mailbox, notice = _mailbox_or_notice(request)
    if notice is not None:
        raise Http404()
    return mailbox


@login_required
def inbox(request: HttpRequest) -> HttpResponse:
    mailbox, notice = _mailbox_or_notice(request)
    if notice is not None:
        return notice
    qs = (
        MessageCopy.objects.filter(mailbox=mailbox, folder=Folder.INBOX)
        .select_related("message")
        .annotate(sort_at=Coalesce("message__sent_at", "created_at"))
        .order_by("-sort_at")
    )
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "mail/inbox.html",
        {"page": page, "folder": Folder.INBOX, "active_nav": Folder.INBOX},
    )


@login_required
def folder_view(request: HttpRequest, folder: str) -> HttpResponse:
    if folder not in Folder.values:
        raise Http404()
    mailbox = _mailbox(request)
    qs = (
        MessageCopy.objects.filter(mailbox=mailbox, folder=folder)
        .select_related("message")
        .annotate(sort_at=Coalesce("message__sent_at", "created_at"))
        .order_by("-sort_at")
    )
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "mail/inbox.html", {"page": page, "folder": folder, "active_nav": folder})


@login_required
def message_detail(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    msg = copy.message
    html_body = ""
    if msg.blob_id and not msg.unretrievable:
        import email
        from email import policy

        raw = open(msg.blob.path, "rb").read()
        mime = email.message_from_bytes(raw, policy=policy.default)
        part = mime.get_body(preferencelist=("html",))
        if part:
            html_body = sanitize_html(part.get_content() or "")
    if request.GET.get("load_images") == "1" and html_body:
        html_body = sanitize_html(html_body, allow_remote_images=True)
    if copy.is_unread:
        copy.is_unread = False
        copy.save(update_fields=["is_unread"])
    return render(
        request,
        "mail/message.html",
        {
            "copy": copy,
            "message": msg,
            "html_body": html_body,
            "bcc_for_view": copy.bcc_snapshot,
            "attachments": msg.attachments.all(),
            "active_nav": copy.folder,
        },
    )


@login_required
def search(request: HttpRequest) -> HttpResponse:
    mailbox = _mailbox(request)
    q = (request.GET.get("q") or "").strip()
    qs = MessageCopy.objects.filter(mailbox=mailbox).select_related("message")
    if q:
        qs = qs.filter(
            models.Q(message__subject__icontains=q)
            | models.Q(message__from_address__icontains=q)
            | models.Q(message__body_text_index__icontains=q)
            | models.Q(message__to_index__icontains=q)
        )
        qs = qs.annotate(sort_at=Coalesce("message__sent_at", "created_at")).order_by("-sort_at")
    else:
        qs = qs.none()
    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "mail/search.html",
        {"page": page, "q": q, "folder": Folder.INBOX, "active_nav": ""},
    )


@login_required
def compose(request: HttpRequest) -> HttpResponse:
    mailbox = _mailbox(request)
    if request.method == "POST":
        to_raw = request.POST.get("to", "")
        to = [x.strip() for x in to_raw.split(",") if x.strip()]
        try:
            send_compose(
                mailbox,
                from_address=request.POST.get("from", mailbox.address),
                to=to,
                subject=request.POST.get("subject", ""),
                text=request.POST.get("body", ""),
            )
            messages.success(request, "Message queued.")
            return redirect("mail_folder", folder="sent")
        except Exception as exc:
            messages.error(request, str(exc))
    return render(request, "mail/compose.html", {"mailbox": mailbox, "active_nav": "compose"})


@login_required
def reply(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    msg = copy.message
    if request.method == "POST":
        send_compose(
            mailbox,
            from_address=mailbox.address,
            to=[msg.reply_to or msg.from_address],
            subject=f"Re: {msg.subject}",
            text=request.POST.get("body", ""),
            in_reply_to=msg.message_id,
            references=msg.message_id,
        )
        return redirect("mail_message", copy_id=copy.id)
    return render(
        request,
        "mail/compose.html",
        {"mailbox": mailbox, "prefill": f"Re: {msg.subject}", "active_nav": "compose"},
    )


@login_required
def reply_all(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    to_list, cc_list, bcc_list = reply_all_recipients(copy, mailbox)
    if request.method == "POST":
        send_compose(
            mailbox,
            from_address=mailbox.address,
            to=to_list,
            cc=cc_list,
            bcc=bcc_list if bcc_list else None,
            subject=f"Re: {copy.message.subject}",
            text=request.POST.get("body", ""),
            in_reply_to=copy.message.message_id,
            references=copy.message.message_id,
        )
        return redirect("mail_message", copy_id=copy.id)
    return render(request, "mail/compose.html", {"mailbox": mailbox, "active_nav": "compose"})


@login_required
def mark_junk(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    copy.folder = Folder.JUNK
    copy.save(update_fields=["folder"])
    return redirect("mail_message", copy_id=copy.id)


@login_required
def mark_not_junk(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    copy.folder = Folder.INBOX
    copy.save(update_fields=["folder"])
    return redirect("mail_message", copy_id=copy.id)


def _redirect_to_folder(folder: str) -> HttpResponse:
    if folder == Folder.INBOX:
        return redirect("mail_inbox")
    return redirect("mail_folder", folder=folder)


@login_required
def trash_message(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    source_folder = copy.folder
    move_to_trash(copy)
    if source_folder == Folder.TRASH:
        return redirect("mail_folder", folder=Folder.TRASH)
    return _redirect_to_folder(source_folder)


@login_required
@require_POST
def purge_message(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox, folder=Folder.TRASH)
    purge_message_copy(copy)
    messages.success(request, "Message deleted permanently.")
    return redirect("mail_folder", folder=Folder.TRASH)


@login_required
def restore_message(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox, folder=Folder.TRASH)
    restore_from_trash(copy)
    return redirect("mail_folder", folder=Folder.INBOX)


@login_required
@require_POST
def empty_trash_view(request: HttpRequest) -> HttpResponse:
    mailbox = _mailbox(request)
    n = empty_trash(mailbox)
    if n:
        messages.success(request, f"Deleted {n} message(s) permanently.")
    else:
        messages.info(request, "Trash is already empty.")
    return redirect("mail_folder", folder=Folder.TRASH)


@login_required
def export_eml(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    msg = copy.message
    if not msg.blob_id:
        raise Http404()
    return FileResponse(open(msg.blob.path, "rb"), as_attachment=True, filename="message.eml")


@login_required
def download_attachment(request: HttpRequest, copy_id: int, attachment_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    att = get_object_or_404(MessageAttachment, pk=attachment_id, message=copy.message)
    if att.blob_id:
        if not SHA256_RE.match(att.blob.sha256):
            raise Http404()
        return FileResponse(open(att.blob.path, "rb"), as_attachment=True, filename=att.filename)
    raise Http404()
