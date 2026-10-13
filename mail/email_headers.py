from __future__ import annotations

import re
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser

_MSG_ID_TOKEN = re.compile(r"<[^>]+>")


def parse_thread_headers(raw: bytes) -> dict[str, str]:
    mime = BytesParser(policy=policy.default).parsebytes(raw)
    return {
        "message_id": _header_value(mime, "Message-ID"),
        "in_reply_to": _header_value(mime, "In-Reply-To"),
        "references": _header_value(mime, "References"),
    }


def _header_value(mime: EmailMessage, name: str) -> str:
    value = mime.get(name)
    if not value:
        return ""
    return str(value).strip()


def reference_ids(*fields: str | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for field in fields:
        if not field:
            continue
        for token in _MSG_ID_TOKEN.findall(field):
            tid = token.strip()
            if tid and tid not in seen:
                seen.add(tid)
                ordered.append(tid)
        for token in field.split():
            tid = token.strip()
            if tid and tid not in seen and ("@" in tid or tid.startswith("<")):
                seen.add(tid)
                ordered.append(tid)
    return ordered
