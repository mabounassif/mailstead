#!/usr/bin/env python3
"""Seed demo data, run a local server, and capture PNG screenshots.

Writes login, inbox, and compose shots to docs/assets/screenshots/.
Requires Playwright Chromium: pip install playwright && playwright install chromium
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "screenshots"
SEED_PATH = ROOT / "scripts" / "seed_demo_screenshots.py"


def _load_seed():
    spec = importlib.util.spec_from_file_location("seed_demo_screenshots", SEED_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load {SEED_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _wait_for_server(url: str, timeout: float = 20) -> None:
    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
        time.sleep(0.2)
    raise SystemExit(f"Server did not become ready at {url}: {last_error}")


def _login(page, base: str, username: str, password: str) -> None:
    page.goto(f"{base}/accounts/login/", wait_until="domcontentloaded")
    page.locator("#id_username").fill(username)
    page.locator("#id_password").fill(password)
    page.locator('button[type="submit"]').click()
    page.wait_for_url("**/mail/**", timeout=15000)
    page.locator(".message-list").wait_for(timeout=15000)


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "Install playwright: pip install playwright && playwright install chromium"
        )

    os.chdir(ROOT)
    seed = _load_seed()
    env = seed.apply_screenshot_env()
    port = os.environ.get("SCREENSHOT_PORT", seed.DEFAULT_PORT)
    base = os.environ.get("SCREENSHOT_BASE_URL", f"http://127.0.0.1:{port}")

    subprocess.check_call(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        cwd=ROOT,
        env=env,
    )
    subprocess.check_call(
        [sys.executable, "manage.py", "createcachetable"],
        cwd=ROOT,
        env=env,
    )
    seed.seed()

    server = subprocess.Popen(
        [
            sys.executable,
            "manage.py",
            "runserver",
            f"127.0.0.1:{port}",
            "--noreload",
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_server(f"{base}/healthz")
        OUT.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=2,
            )
            page.emulate_media(color_scheme="light")

            page.goto(f"{base}/accounts/login/", wait_until="domcontentloaded")
            page.locator(".auth-card").wait_for()
            page.locator(".app-brand-icon").wait_for()
            page.locator("h1").click()
            page.wait_for_timeout(300)
            login_path = OUT / "login.png"
            page.screenshot(path=str(login_path), full_page=False)
            print(f"wrote {login_path}")

            _login(page, base, seed.DEMO_USER, seed.DEMO_PASS)
            page.goto(f"{base}/mail/", wait_until="domcontentloaded")
            page.locator(".message-list").wait_for()
            page.get_by_text("Q4 planning").wait_for()
            page.wait_for_timeout(300)
            inbox_path = OUT / "inbox.png"
            page.screenshot(path=str(inbox_path), full_page=False)
            print(f"wrote {inbox_path}")

            page.locator("a.sidebar-compose").click()
            page.wait_for_url("**/mail/compose/**", timeout=15000)
            panel = page.locator(".compose-panel")
            panel.wait_for()
            page.locator("#to").fill("alice@partner.com")
            page.locator("#subject").fill("Re: Q4 planning")
            page.locator("#body").fill(
                "Tuesday at 2pm works on our side. I'll send a short agenda beforehand."
            )
            page.locator("#body").blur()
            page.wait_for_timeout(300)
            compose_path = OUT / "compose.png"
            page.screenshot(path=str(compose_path), full_page=False)
            print(f"wrote {compose_path}")

            browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=8)
        except subprocess.TimeoutExpired:
            server.kill()


if __name__ == "__main__":
    main()
