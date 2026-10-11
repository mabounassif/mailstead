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
