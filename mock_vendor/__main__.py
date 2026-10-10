"""Runnable mock enterprise API (NOT production spam filtering)."""

from __future__ import annotations

import json
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PRIVATE_KEY = Ed25519PrivateKey.generate()
PUBLIC_PEM = PRIVATE_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()


def _token(installation_id: str, capabilities: list[str]) -> str:
    return jwt.encode(
        {
            "iss": "mock-vendor",
            "aud": installation_id,
            "exp": 9999999999,
            "capabilities": capabilities,
            "entitlements_version": 1,
        },
        PRIVATE_KEY,
        algorithm="EdDSA",
    )


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        payload = json.loads(raw.decode() or "{}")
        if self.path == "/v1/activate":
            iid = payload.get("installation_id", str(uuid.uuid4()))
            cred = str(uuid.uuid4())
            self._json(200, {"service_credential": cred, "entitlement_token": _token(iid, ["spam_filtering"])})
            return
        if self.path == "/v1/entitlements/refresh":
            self._json(200, {"entitlement_token": _token("test-install", ["spam_filtering"])})
            return
        if self.path == "/v1/spam/classify":
            mime = payload.get("mime_b64") or ""
            verdict = "spam" if "MOCK-SPAM" in mime else "ham"
            self._json(
                200,
                {
                    "verdict": verdict,
                    "score": 0.99 if verdict == "spam" else 0.01,
                    "reasons": ["keyword"] if verdict == "spam" else [],
                    "service": "mock-vendor (NOT a real spam filter)",
                    "engine_version": "mock-1",
                    "model_version": "mock-1",
                },
            )
            return
        self._json(404, {"error": "not found"})


def main():
    host, port = "127.0.0.1", 8765
    print(f"Mock vendor on http://{host}:{port}")
    print("Public key PEM for ENTERPRISE_PUBLIC_KEYS:\n", PUBLIC_PEM)
    HTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
