#!/usr/bin/env python3
"""Validate template config and refresh marketplace metadata via Railway CLI.

Railway does not expose template serializedConfig updates on the public GraphQL API.
After merging icon/assets to main, apply service icons and variable descriptions in the
template composer (paste from railway/mailstead.serialized-config.json or set fields manually).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "railway" / "mailstead.serialized-config.json"
README = ROOT / "docs" / "railway-template-readme.md"
TEMPLATE_CODE = "mailstead"
ICON_URL = (
    "https://raw.githubusercontent.com/mabounassif/mailstead/main/"
    "docs/assets/mailstead-template-icon.png"
)


def _load_config() -> dict:
    data = json.loads(CONFIG.read_text())
    if not data.get("services"):
        raise SystemExit("serialized config must include services")
    for svc in data["services"].values():
        if not svc.get("icon"):
            raise SystemExit(f"service {svc.get('name')} is missing icon")
        for name, var in (svc.get("variables") or {}).items():
            if not (var or {}).get("description"):
                raise SystemExit(f"variable {name} is missing description")
    return data


def _publish_metadata() -> None:
    cmd = [
        "railway",
        "templates",
        "publish",
        TEMPLATE_CODE,
        "--category",
        "Other",
        "--description",
        "Self-hosted Resend webmail for small teams. Django app with /data volume.",
        "--readme-file",
        str(README),
        "--image",
        ICON_URL,
        "--json",
    ]
    subprocess.run(cmd, check=True)


def _diff_live() -> None:
    import json as _json

    proc = subprocess.run(
        [
            "railway",
            "api",
            'query { template(code: "mailstead") { serializedConfig } }',
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    live = _json.loads(proc.stdout)["data"]["template"]["serializedConfig"]
    want = _json.loads(CONFIG.read_text())
    svc_id = next(iter(want["services"]))
    live_svc = live["services"].get(svc_id, {})
    want_svc = want["services"][svc_id]
    if live_svc.get("icon") != want_svc.get("icon"):
        print(f"icon: live={live_svc.get('icon')!r} want={want_svc.get('icon')!r}")
    for key, want_var in want_svc.get("variables", {}).items():
        live_var = (live_svc.get("variables") or {}).get(key) or {}
        if not live_var.get("description"):
            print(f"missing description: mailstead.{key}")
        elif live_var.get("description") != want_var.get("description"):
            print(f"description drift: {key}")


def main() -> None:
    _load_config()
    print(f"OK: {CONFIG} validates (icons + variable descriptions).")
    if "--diff" in sys.argv:
        print()
        print("Diff vs published template:")
        _diff_live()
    print()
    print("Apply in Railway template composer:")
    print("  Workspace → Templates → mailstead → Edit")
    print("  - Template icon: use transparent PNG URL (see serialized config)")
    print("  - mailstead service → Update Info → Icon → same URL")
    print("  - Variables: add descriptions and defaults from railway/mailstead.serialized-config.json")
    print()
    if "--publish-metadata" in sys.argv:
        print("Publishing marketplace readme, description, and card image...")
        _publish_metadata()
        print("Done.")
    else:
        print("Run with --publish-metadata to update marketplace card via CLI.")


if __name__ == "__main__":
    main()
