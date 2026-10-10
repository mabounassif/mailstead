import logging
import re

REDACT_PATTERNS = [
    re.compile(r"(?i)(password|token|secret|api[_-]?key|authorization)\s*[=:]\s*\S+"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-+/=]+\b"),
    re.compile(r"\bre_[A-Za-z0-9]+\b"),
]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            msg = record.msg
            for pat in REDACT_PATTERNS:
                msg = pat.sub(lambda m: m.group(0)[: m.group(0).index("=") + 1] + "[REDACTED]" if "=" in m.group(0) else "[REDACTED]", msg)
            record.msg = msg
        return True
