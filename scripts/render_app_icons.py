#!/usr/bin/env python3
"""Export app and Railway template icons from docs/assets/mailstead-brand.svg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "core" / "static" / "mailstead"
DOC = ROOT / "docs" / "assets"
BRAND_SVG = DOC / "mailstead-brand.svg"
SIZES = (512, 192, 180)
INKSCAPE = shutil.which("inkscape")


def _export_png(svg: Path, out: Path, size: int) -> None:
    if not INKSCAPE:
        raise SystemExit("inkscape is required to export PNG icons (install inkscape or use snap)")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            INKSCAPE,
            str(svg),
            f"--export-filename={out}",
            "-w",
            str(size),
            "-h",
            str(size),
        ],
        check=True,
    )


def main() -> None:
    if not BRAND_SVG.is_file():
        raise SystemExit(f"Missing {BRAND_SVG}")
    for size in SIZES:
        out = STATIC / f"icon-{size}.png"
        _export_png(BRAND_SVG, out, size)
        print(f"wrote {out}")
    template_icon = DOC / "mailstead-template-icon.png"
    _export_png(BRAND_SVG, template_icon, 512)
    print(f"wrote {template_icon}")
    # Legacy JPEG used by some docs; keep in sync for non-SVG consumers.
    try:
        from PIL import Image

        Image.open(template_icon).convert("RGB").save(DOC / "mailstead-template-logo.jpg", quality=92)
        Image.open(template_icon).convert("RGB").save(STATIC / "icon-source.jpg", quality=92)
    except ImportError:
        pass


if __name__ == "__main__":
    main()
