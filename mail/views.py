from __future__ import annotations

import re
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from django.views.decorators.http import require_POST

from mail.chats import (
    ALL_THREADS,
    compose_subject,
    contact_chats,
    contact_key,
    contact_messages,
    conversation_for_people,
    direct_message_for_people,
    conversation_messages,
    counterparty,
    detach_catchall,
    group_messages,
    people_key,
    people_label,
    thread_value,
)
from mail.compose import reply_all_recipients, send_compose
from mail.conversations import (
    active_cc_addresses,
    attach_to_parent,
    conversation_for_topic,
    discard_failed_spec,
    ensure_mailbox_conversations,
    finalize_chat_send,
    known_addresses,
    plan_chat_send,
    with_events,
)
from mail.threading import copy_is_outgoing, effective_message_id, reference_chain, thread_copies, topic_is_generic, topic_key
from mail.deletion import empty_trash, move_to_trash, purge_message_copy, restore_from_trash
from accounts.models import Mailbox
from mail.models import Conversation, ConversationEvent, Folder, Message, MessageAttachment, MessageCopy, Project

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


def _message_html_body(msg: Message, *, load_images: bool) -> str:
    if not msg.blob_id or msg.unretrievable:
        return ""
    import email
    from email import policy

    from mail.html_safety import sanitize_html, wrap_html_for_iframe

    raw = open(msg.blob.path, "rb").read()
    mime = email.message_from_bytes(raw, policy=policy.default)
    part = mime.get_body(preferencelist=("html",))
    if not part:
        return ""
    html_body = sanitize_html(part.get_content() or "")
    if load_images:
        html_body = sanitize_html(html_body, allow_remote_images=True)
    return wrap_html_for_iframe(html_body)


def _thread_items(
    anchor: MessageCopy,
    mailbox: Mailbox,
    *,
    load_images: bool,
) -> list[dict]:
    items: list[dict] = []
    for thread_copy in thread_copies(anchor):
        msg = thread_copy.message
        items.append(
            {
                "kind": "message",
                "copy": thread_copy,
                "message": msg,
                "html_body": _message_html_body(msg, load_images=load_images),
                "attachments": list(msg.attachments.all()),
                "bcc_for_view": thread_copy.bcc_snapshot,
                "is_outgoing": copy_is_outgoing(thread_copy, mailbox),
                "is_anchor": thread_copy.id == anchor.id,
                "sort_at": msg.sent_at or thread_copy.created_at,
            }
        )
    conv_ids = [item["message"].conversation_id for item in items if item["message"].conversation_id]
    for event in ConversationEvent.objects.filter(conversation_id__in=conv_ids):
        items.append({"kind": "event", "body": event.body, "sort_at": event.created_at})
    items.sort(key=lambda item: item["sort_at"])
    count = len(items)
    for index, item in enumerate(items):
        item["starts_expanded"] = count <= 1 or index == count - 1
    return items


def _reply_recipient_context(copy: MessageCopy, mailbox: Mailbox) -> dict[str, str]:
    msg = copy.message
    to_list, cc_list, _bcc = reply_all_recipients(copy, mailbox)
    return {
        "reply_to_address": msg.reply_to or msg.from_address,
        "reply_all_to": ", ".join(to_list),
        "reply_all_cc": ", ".join(cc_list),
        "reply_subject": f"Re: {msg.subject}",
    }


def _compose_reply_render(
    request: HttpRequest,
    copy: MessageCopy,
    mailbox: Mailbox,
    *,
    title: str,
    prefill_to: str,
    prefill_cc: str = "",
) -> HttpResponse:
    rctx = _reply_recipient_context(copy, mailbox)
    return render(
        request,
        "mail/compose.html",
        {
            "mailbox": mailbox,
            "prefill": rctx["reply_subject"],
            "prefill_to": prefill_to,
            "prefill_cc": prefill_cc,
            "compose_title": title,
            "close_href": reverse("mail_message", args=[copy.id]),
            "active_nav": copy.folder,
        },
    )


@login_required
def inbox(request: HttpRequest) -> HttpResponse:
    mailbox, notice = _mailbox_or_notice(request)
    if notice is not None:
        return notice
    detach_catchall(mailbox)
    ensure_mailbox_conversations(mailbox)
    new_kind = (request.GET.get("new") or "").strip()
    if new_kind in ("1", "channel", "message"):
        return _new_chat(request, mailbox, kind="message" if new_kind == "message" else "channel")
    selected = None
    raw_project = request.GET.get("project")
    if raw_project and raw_project.isdigit():
        selected = Project.objects.filter(mailbox=mailbox, pk=int(raw_project)).first()
    contact_address = (request.GET.get("contact") or "").strip()
    raw_dm = (request.GET.get("dm") or "").strip()
    thread = (request.GET.get("thread") or "").strip()
    if thread == ALL_THREADS:
        thread = ""
    raw_channel = (request.GET.get("channel") or "").strip()
    open_conv = None
    if raw_channel.isdigit():
        open_conv = Conversation.objects.filter(mailbox=mailbox, pk=int(raw_channel)).first()
    if open_conv is not None and not contact_address and selected is None:
        mode = "channel"
        chats = conversation_messages(mailbox, open_conv)
        contact_label = open_conv.topic
        thread = open_conv.topic_key
    elif raw_dm and selected is None:
        mode = "dm"
        open_conv = conversation_for_people(mailbox, raw_dm)
        chats = conversation_messages(mailbox, open_conv) if open_conv is not None else []
        contact_label = people_label(open_conv, mailbox) if open_conv is not None else raw_dm
        if open_conv is not None:
            thread = open_conv.topic_key
    elif selected is not None:
        mode = "group"
        chats = group_messages(mailbox, selected)
        contact_label = ""
    elif contact_address:
        mode = "dm"
        contact_label, _all = contact_messages(mailbox, contact_address)
        if not contact_label:
            contact_label = contact_address
        if thread:
            open_conv = conversation_for_topic(
                mailbox,
                thread,
                contact=contact_key(contact_address),
                project=None,
            )
        if open_conv is None:
            open_conv = (
                Conversation.objects.filter(
                    mailbox=mailbox,
                    participants__address=contact_key(contact_address),
                    participants__active=True,
                )
                .distinct()
                .order_by("-id")
                .first()
            )
        chats = conversation_messages(mailbox, open_conv) if open_conv is not None else []
        if open_conv is not None:
            thread = open_conv.topic_key
            contact_label = people_label(open_conv, mailbox) or contact_label
    else:
        mode = "contacts"
        chats = contact_chats(mailbox)
        contact_label = ""
    if mode in ("dm", "channel", "group") and request.method == "POST":
        bound_thread = thread if (raw_channel or raw_dm or request.GET.get("thread") or mode == "channel") else ""
        sent = _send_chat_message(
            request,
            mailbox,
            mode="contact" if mode == "dm" else ("group" if mode == "group" else "contact"),
            chats=chats,
            contact_address=contact_key(contact_address) if contact_address else _primary_contact(open_conv, mailbox),
            project=selected,
            thread=bound_thread,
            return_dm=people_key(open_conv, mailbox) if mode == "dm" and open_conv is not None else "",
        )
        if sent is not None:
            return sent
    visible = with_events(chats) if mode in ("dm", "channel", "group") else chats
    can_compose = open_conv is not None or (mode == "group" and bool(chats))
    if mode == "group" and open_conv is None and thread:
        open_conv = conversation_for_topic(mailbox, thread, project=selected)
    participants = list(open_conv.participants.filter(active=True)) if open_conv is not None else []
    topic_value = open_conv.topic if open_conv is not None else ""
    return render(
        request,
        "mail/chats.html",
        {
            "folder": Folder.INBOX,
            "active_nav": Folder.INBOX,
            "selected_project": selected,
            "mode": mode,
            "chats": visible,
            "contact_label": contact_label,
            "contact_address": contact_key(contact_address) if contact_address else "",
            "thread_filter": thread,
            "compose_subject": topic_value,
            "can_compose": can_compose,
            "participants": participants,
            "known_addresses": known_addresses(mailbox) if mode in ("dm", "channel", "group", "new") else [],
            "show_subjects": False,
            "open_channel": open_conv.id if open_conv is not None else None,
            "active_dm": people_key(open_conv, mailbox) if mode == "dm" and open_conv is not None else "",
            "chat_base_url": _chat_url(
                contact=contact_key(contact_address) if contact_address else "",
                project_id=selected.id if selected is not None else None,
            ),
        },
    )


def _primary_contact(conversation, mailbox) -> str:
    if conversation is None:
        return ""
    own = (mailbox.address or "").casefold()
    for part in conversation.participants.filter(active=True).order_by("id"):
        if part.address != own:
            return part.address
    return ""


def _chat_url(*, contact: str = "", project_id: int | None = None, thread: str = "", channel_id: int | None = None) -> str:
    params: dict[str, str] = {}
    if channel_id:
        params["channel"] = str(channel_id)
    elif project_id:
        params["project"] = str(project_id)
    elif contact:
        params["contact"] = contact
    elif thread and thread != ALL_THREADS:
        params["thread"] = thread
    query = urlencode(params)
    url = reverse("mail_inbox")
    return f"{url}?{query}" if query else url


def _reply_header_kwargs(msg) -> dict:
    mid = effective_message_id(msg)
    if not mid:
        return {}
    return {"in_reply_to": mid, "references": reference_chain(msg) or mid}


def _send_kwargs(spec) -> dict:
    kwargs = {}
    if spec.cc:
        kwargs["cc"] = spec.cc
    if spec.bcc:
        kwargs["bcc"] = spec.bcc
    if spec.in_reply_to:
        kwargs["in_reply_to"] = spec.in_reply_to
    if spec.references:
        kwargs["references"] = spec.references
    return kwargs


def _send_chat_message(request, mailbox, *, mode, chats, contact_address, project, thread, return_dm=""):
    body = request.POST.get("body") or ""
    subject = (request.POST.get("subject") or "").strip()
    try:
        spec = plan_chat_send(
            mailbox,
            mode=mode,
            chats=chats,
            contact_address=contact_address,
            project=project,
            thread=thread,
            subject=subject,
            body=body,
            add_raw=request.POST.get("add") or "",
            drop_raw=request.POST.get("drop") or "",
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return None
    try:
        outbound = send_compose(
            mailbox,
            from_address=mailbox.address,
            to=spec.to,
            subject=spec.subject,
            text=spec.text,
            **_send_kwargs(spec),
        )
    except Exception as exc:
        discard_failed_spec(spec)
        messages.error(request, str(exc))
        return None
    finalize_chat_send(mailbox, outbound, spec)
    messages.success(request, "Message queued.")
    if return_dm:
        return redirect(f"{reverse('mail_inbox')}?dm={return_dm}")
    if spec.conversation is not None:
        return redirect(_chat_url(channel_id=spec.conversation.id))
    return redirect(
        _chat_url(
            contact=contact_address,
            project_id=project.id if project is not None else None,
            thread=thread_value(spec.subject),
        )
    )


def _queue_new_conversation(request, mailbox, recipients, subject, body, *, as_dm=False):
    spec = None
    try:
        spec = plan_chat_send(
            mailbox,
            mode="new",
            chats=[],
            contact_address=contact_key(recipients[0]),
            project=None,
            thread="",
            subject=subject,
            body=body,
            add_raw=request.POST.get("add") or "",
            extra_to=recipients,
        )
        outbound = send_compose(
            mailbox,
            from_address=mailbox.address,
            to=spec.to,
            subject=spec.subject,
            text=spec.text,
            **_send_kwargs(spec),
        )
        finalize_chat_send(mailbox, outbound, spec)
        if as_dm and spec.conversation is not None:
            spec.conversation.topic_key = "dm:" + people_key(spec.conversation, mailbox)
            spec.conversation.save(update_fields=["topic_key"])
        messages.success(request, "Message queued.")
        if as_dm and spec.conversation is not None:
            return redirect(f"{reverse('mail_inbox')}?dm={people_key(spec.conversation, mailbox)}")
        if spec.conversation is not None:
            return redirect(_chat_url(channel_id=spec.conversation.id))
        return redirect("mail_inbox")
    except ValueError as exc:
        messages.error(request, str(exc))
    except Exception as exc:
        if spec is not None:
            discard_failed_spec(spec)
        messages.error(request, str(exc))
    return None


def _send_into_channel(request, mailbox, channel_id: int, body: str):
    conversation = Conversation.objects.filter(mailbox=mailbox, pk=channel_id).first()
    if conversation is None:
        messages.error(request, "Choose a channel.")
        return None
    if not body.strip():
        messages.error(request, "Write a message first.")
        return None
    posted = request.POST.copy()
    posted["body"] = body
    posted["subject"] = conversation.topic
    request.POST = posted
    return _send_chat_message(
        request,
        mailbox,
        mode="contact",
        chats=conversation_messages(mailbox, conversation),
        contact_address=_primary_contact(conversation, mailbox),
        project=None,
        thread=conversation.topic_key,
    )


def _continue_direct(request, mailbox, conversation, body: str):
    saved = conversation.topic_key
    normal = topic_key(conversation.topic)
    conversation.topic_key = normal
    conversation.save(update_fields=["topic_key"])
    posted = request.POST.copy()
    posted["body"] = body
    posted["subject"] = conversation.topic
    request.POST = posted
    try:
        return _send_chat_message(
            request,
            mailbox,
            mode="contact",
            chats=conversation_messages(mailbox, conversation),
            contact_address=_primary_contact(conversation, mailbox),
            project=None,
            thread=normal,
            return_dm=people_key(conversation, mailbox),
        )
    finally:
        conversation.topic_key = saved
        conversation.save(update_fields=["topic_key"])


def _new_chat(request: HttpRequest, mailbox, *, kind: str = "message") -> HttpResponse:
    draft_to = ""
    draft_body = ""
    draft_subject = ""
    draft_channel = ""
    if request.method == "POST":
        draft_body = (request.POST.get("body") or "").strip()
        draft_subject = (request.POST.get("subject") or "").strip()
        draft_to = (request.POST.get("to") or "").strip()
        recipients = [part.strip() for part in draft_to.split(",") if part.strip()]
        if not draft_body:
            messages.error(request, "Write a message first.")
        elif not recipients:
            messages.info(request, "Add at least one participant.")
        elif draft_subject:
            sent = _queue_new_conversation(request, mailbox, recipients, draft_subject, draft_body)
            if sent is not None:
                return sent
        else:
            key = ",".join(sorted(contact_key(item) for item in recipients))
            existing = direct_message_for_people(mailbox, key)
            if existing is not None:
                sent = _continue_direct(request, mailbox, existing, draft_body)
                if sent is not None:
                    return sent
            else:
                label = ", ".join(contact_key(item).split("@")[0] for item in recipients)
                sent = _queue_new_conversation(request, mailbox, recipients, label, draft_body, as_dm=True)
                if sent is not None:
                    return sent
    return render(
        request,
        "mail/chats.html",
        {
            "folder": Folder.INBOX,
            "active_nav": Folder.INBOX,
            "selected_project": None,
            "mode": "new",
            "new_kind": kind,
            "new_message": True,
            "chats": [],
            "contact_label": "",
            "contact_address": "",
            "reply_copy": None,
            "draft_to": draft_to,
            "draft_body": draft_body,
            "draft_subject": draft_subject,
            "draft_channel": draft_channel,
            "participants": [],
            "known_addresses": known_addresses(mailbox),
        },
    )


@login_required
def folder_view(request: HttpRequest, folder: str) -> HttpResponse:
    if folder not in Folder.values:
        raise Http404()
    if folder in (Folder.SENT, Folder.DRAFTS, Folder.ARCHIVE):
        return redirect("mail_inbox")
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
    load_images = request.GET.get("load_images") == "1"
    thread = _thread_items(copy, mailbox, load_images=load_images)
    html_body = ""
    for item in thread:
        if item["is_anchor"]:
            html_body = item["html_body"]
            break
    if copy.is_unread:
        copy.is_unread = False
        copy.save(update_fields=["is_unread"])
    compose_mode = request.GET.get("compose", "")
    if compose_mode not in ("reply", "reply-all"):
        compose_mode = ""
    who = counterparty(msg, mailbox.address)
    thread_contact = "" if copy.project_id else contact_key(who)
    if copy.folder in (Folder.SENT, Folder.DRAFTS, Folder.ARCHIVE, Folder.INBOX):
        back_url = reverse("mail_inbox")
        if copy.project_id:
            back_url = f"{back_url}?project={copy.project_id}"
            back_label = copy.project.name
        else:
            back_url = f"{back_url}?contact={thread_contact}"
            back_label = "Messages"
    else:
        back_url = reverse("mail_folder", args=[copy.folder])
        back_label = copy.get_folder_display()
    return render(
        request,
        "mail/message.html",
        {
            "copy": copy,
            "message": msg,
            "back_url": back_url,
            "back_label": back_label,
            "thread": thread,
            "html_body": html_body,
            "bcc_for_view": copy.bcc_snapshot,
            "attachments": msg.attachments.all(),
            "active_nav": Folder.INBOX
            if copy.folder in (Folder.INBOX, Folder.SENT, Folder.DRAFTS, Folder.ARCHIVE)
            else copy.folder,
            "selected_project": copy.project if copy.project_id else None,
            "contact_address": thread_contact,
            "mailbox": mailbox,
            "can_reply": copy.folder != Folder.TRASH,
            "compose_mode": compose_mode,
            "thread_message_count": sum(1 for item in thread if item.get("kind") != "event"),
            **_reply_recipient_context(copy, mailbox),
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
        subject = request.POST.get("subject", "")
        if topic_is_generic(subject):
            messages.error(request, "Add a topic before sending.")
            return render(request, "mail/compose.html", {"mailbox": mailbox, "active_nav": "compose"})
        try:
            send_compose(
                mailbox,
                from_address=request.POST.get("from", mailbox.address),
                to=to,
                subject=subject,
                text=request.POST.get("body", ""),
            )
            messages.success(request, "Message queued.")
            return redirect("mail_inbox")
        except Exception as exc:
            messages.error(request, str(exc))
    return render(request, "mail/compose.html", {"mailbox": mailbox, "active_nav": "compose"})


@login_required
def reply(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    msg = copy.message
    if request.method == "POST":
        to_addr = msg.reply_to or msg.from_address
        headers = _reply_header_kwargs(msg)
        cc = active_cc_addresses(msg, mailbox, [to_addr])
        outbound = send_compose(
            mailbox,
            from_address=mailbox.address,
            to=[to_addr],
            cc=cc or None,
            subject=f"Re: {msg.subject}",
            text=request.POST.get("body", ""),
            **headers,
        )
        attach_to_parent(mailbox, outbound, msg)
        messages.success(request, "Reply queued.")
        return redirect("mail_message", copy_id=copy.id)
    if request.GET.get("full") == "1":
        rctx = _reply_recipient_context(copy, mailbox)
        return _compose_reply_render(
            request,
            copy,
            mailbox,
            title="Reply",
            prefill_to=rctx["reply_to_address"],
        )
    return redirect(f"{reverse('mail_message', args=[copy_id])}?compose=reply")


@login_required
def reply_all(request: HttpRequest, copy_id: int) -> HttpResponse:
    mailbox = _mailbox(request)
    copy = get_object_or_404(MessageCopy, pk=copy_id, mailbox=mailbox)
    to_list, cc_list, bcc_list = reply_all_recipients(copy, mailbox)
    if request.method == "POST":
        outbound = send_compose(
            mailbox,
            from_address=mailbox.address,
            to=to_list,
            cc=cc_list,
            bcc=bcc_list if bcc_list else None,
            subject=f"Re: {copy.message.subject}",
            text=request.POST.get("body", ""),
            **_reply_header_kwargs(copy.message),
        )
        attach_to_parent(mailbox, outbound, copy.message)
        messages.success(request, "Reply queued.")
        return redirect("mail_message", copy_id=copy.id)
    if request.GET.get("full") == "1":
        rctx = _reply_recipient_context(copy, mailbox)
        return _compose_reply_render(
            request,
            copy,
            mailbox,
            title="Reply all",
            prefill_to=rctx["reply_all_to"],
            prefill_cc=rctx["reply_all_cc"],
        )
    return redirect(f"{reverse('mail_message', args=[copy_id])}?compose=reply-all")


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
