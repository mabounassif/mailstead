from __future__ import annotations

import re

import nh3

ALLOWED_TAGS = {
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "code",
    "div",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
    "img",
}

REMOTE_IMG_RE = re.compile(r"""<img[^>]+src=["']https?://[^"']+["']""", re.I)
_BODY_RE = re.compile(r"<body[^>]*>(.*)</body>", re.I | re.S)

_IFRAME_BASE_CSS = """
html, body { margin: 0; padding: 0; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: #202124;
  overflow-wrap: anywhere;
  word-wrap: break-word;
}
a { color: #1a73e8; }
blockquote {
  margin: 0.75em 0;
  padding-left: 1em;
  border-left: 1px solid #dadce0;
  color: #5f6368;
}
pre, code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9em;
}
img { max-width: 100%; height: auto; }
.blocked-image { color: #5f6368; font-style: italic; }
"""


def _html_body_fragment(html: str) -> str:
    html = (html or "").strip()
    if not html:
        return ""
    match = _BODY_RE.search(html)
    if match:
        return match.group(1).strip()
    return html


def wrap_html_for_iframe(html: str) -> str:
    """Wrap sanitized HTML in a minimal document with consistent base typography."""
    fragment = _html_body_fragment(html)
    if not fragment:
        return ""
    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="utf-8">'
        f"<style>{_IFRAME_BASE_CSS}</style>"
        "</head><body>"
        f"{fragment}"
        "</body></html>"
    )


def sanitize_html(html: str, allow_remote_images: bool = False) -> str:
    cleaned = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes={
            "*": {"class"},
            "a": {"href", "title"},
            "img": {"src", "alt"},
            "td": {"colspan", "rowspan"},
            "th": {"colspan", "rowspan"},
        },
    )
    if not allow_remote_images:
        cleaned = REMOTE_IMG_RE.sub('<span class="blocked-image">[image blocked]</span>', cleaned)
    return cleaned
