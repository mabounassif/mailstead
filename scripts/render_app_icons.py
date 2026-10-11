#!/usr/bin/env python3
"""Resize icon-source.jpg into Home Screen PNG sizes (no redraw)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "core" / "static" / "mailstead"
DOC = Path(__file__).resolve().parent.parent / "docs" / "assets"
SOURCE = ROOT / "icon-source.jpg"
SIZES = (512, 192, 180)
TEMPLATE_ICON = DOC / "mailstead-template-icon.png"


def _square(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    if w == h:
        return img
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side))


def _transparent_template_icon(base: Image.Image, size: int = 512) -> Image.Image:
    rgba = base.convert("RGBA")
    pixels = rgba.load()
    w, h = rgba.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r > 240 and g > 240 and b > 240:
                pixels[x, y] = (r, g, b, 0)
            else:
                pixels[x, y] = (r, g, b, 255)
    return rgba.resize((size, size), Image.Resampling.LANCZOS)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Missing {SOURCE} — add your logo as icon-source.jpg first.")
    base = _square(Image.open(SOURCE))
    base.save(SOURCE, quality=95)
    base.save(DOC / "mailstead-template-logo.jpg", quality=95)
    for size in SIZES:
        out = ROOT / f"icon-{size}.png"
        _square(base).resize((size, size), Image.Resampling.LANCZOS).save(out, optimize=True)
        print(f"wrote {out}")
    _transparent_template_icon(base).save(TEMPLATE_ICON, optimize=True)
    print(f"wrote {TEMPLATE_ICON}")


if __name__ == "__main__":
    main()
