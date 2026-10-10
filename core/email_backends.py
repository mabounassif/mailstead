"""Send transactional mail (password reset, etc.) via Resend."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)


class ResendBackend(BaseEmailBackend):
    def send_messages(self, email_messages: list[Any]) -> int:
        if not email_messages:
            return 0
        if not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not set; skipping email send")
            return 0

        import resend

        resend.api_key = settings.RESEND_API_KEY
        sent = 0
        for message in email_messages:
            payload: dict[str, Any] = {
                "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
                "to": list(message.to),
                "subject": message.subject,
            }
            if message.body:
                payload["text"] = message.body
            if getattr(message, "alternatives", None):
                for content, mimetype in message.alternatives:
                    if mimetype == "text/html":
                        payload["html"] = content
            try:
                resend.Emails.send(payload)
                sent += 1
            except Exception:
                logger.exception("Resend send failed for password-reset mail")
                if not self.fail_silently:
                    raise
        return sent
