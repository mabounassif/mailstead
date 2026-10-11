#!/usr/bin/env python3
"""Render PNG home-screen icons from the Mailstead brand palette (run after editing icon.svg)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent / "core" / "static" / "mailstead"
SIZES = (512, 192, 180)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _gradient_bg(size: int) -> Image.Image:
    img = Image.new("RGB", (size, size))
    px = img.load()
    c0 = (30, 58, 138)
    c1 = (37, 99, 235)
    c2 = (59, 130, 246)
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            if t < 0.45:
                u = t / 0.45
                r, g, b = (_lerp(c0[i], c1[i], u) for i in range(3))
            else:
                u = (t - 0.45) / 0.55
                r, g, b = (_lerp(c1[i], c2[i], u) for i in range(3))
            sheen = max(0, 1 - y / (size * 0.55)) * 28
            px[x, y] = (
                min(255, int(r + sheen)),
                min(255, int(g + sheen)),
                min(255, int(b + sheen * 0.5)),
            )
    return img


def _scale(v: float, size: int) -> int:
    return int(v * size / 512)


def draw_icon(size: int) -> Image.Image:
    img = _gradient_bg(size)
    draw = ImageDraw.Draw(img, "RGBA")
    s = size / 512

    # Envelope shadow
    sx, sy = _scale(108, size), _scale(156, size)
    sw, sh = _scale(296, size), _scale(216, size)
    r = _scale(28, size)
    draw.rounded_rectangle((sx, sy + _scale(10, size), sx + sw, sy + sh + _scale(10, size)), r, fill=(15, 23, 42, 70))

    # Body
    draw.rounded_rectangle((sx, sy, sx + sw, sy + sh), r, fill=(248, 250, 252, 255))

    # Inner fold (gray)
    fold = [
        (sx + _scale(24, size), sy + _scale(40, size)),
        (size // 2, sy + _scale(136, size)),
        (sx + sw - _scale(24, size), sy + _scale(40, size)),
        (sx + sw - _scale(24, size), sy + sh - _scale(20, size)),
        (sx + _scale(24, size), sy + sh - _scale(20, size)),
    ]
    draw.polygon(fold, fill=(226, 232, 240, 255))

    # Blue flap
    flap = [
        (sx + _scale(24, size), sy + _scale(40, size)),
        (size // 2, sy + _scale(128, size)),
        (sx + sw - _scale(24, size), sy + _scale(40, size)),
    ]
    draw.polygon(flap, fill=(37, 99, 235, 255))

    # Highlight on flap
    hi = [
        (sx + _scale(24, size), sy + _scale(40, size)),
        (size // 2, sy + _scale(128, size)),
        (size // 2, sy + _scale(118, size)),
        (sx + _scale(32, size), sy + _scale(44, size)),
    ]
    draw.polygon(hi, fill=(255, 255, 255, 120))

    # Accent dot
    cx, cy = size // 2, _scale(392, size)
    rad = max(3, _scale(6, size))
    draw.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=(147, 197, 253, 230))

    return img.convert("RGB")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        path = ROOT / f"icon-{size}.png"
        draw_icon(size).save(path, optimize=True)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
