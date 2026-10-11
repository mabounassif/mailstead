#!/usr/bin/env python3
"""Capture PNG screenshots for the Railway template readme (requires Playwright)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "screenshots"
BASE = os.environ.get("SCREENSHOT_BASE_URL", "http://127.0.0.1:18765")
LOGIN = f"{BASE}/accounts/login/"
INBOX = f"{BASE}/mail/"
COMPOSE = f"{BASE}/mail/compose/"


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Install playwright: pip install playwright && playwright install chromium")

    OUT.mkdir(parents=True, exist_ok=True)
    shots = [
        ("login.png", LOGIN, None),
        ("inbox.png", INBOX, {"username": "demo", "password": "demo-demo-demo"}),
        ("compose.png", COMPOSE, {"username": "demo", "password": "demo-demo-demo"}),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
        for name, url, creds in shots:
            if creds:
                page.goto(LOGIN, wait_until="networkidle")
                page.fill("#id_username", creds["username"])
                page.fill("#id_password", creds["password"])
                page.click('button[type="submit"]')
                page.wait_for_url("**/mail/**", timeout=15000)
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(400)
            path = OUT / name
            page.screenshot(path=str(path), full_page=False)
            print(f"wrote {path}")
        browser.close()


if __name__ == "__main__":
    main()
