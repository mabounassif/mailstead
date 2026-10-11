# Web Push notifications for Mailstead (exploration)

**Date:** 2026-10-11  
**Scope:** Design only — no application changes in this document.  
**Audience:** 10–50 user self-hosted deployments on Railway.

---

## Executive summary

Mailstead today is a **server-rendered Django portal** (HTMX, no client bundle) with **no PWA manifest, service worker, or push infrastructure**. Email arrives via **Resend webhooks → deduplicated `inbound` jobs → `ingest_inbound()`**, which creates `Message` / `MessageCopy` rows. A **single co-located worker** (`manage.py worker`) processes the job queue; there is no Redis, Celery, or third-party push relay.

For **iPhone users**, Web Push is available **only after “Add to Home Screen”** and only when the site behaves as a **standalone web app** (manifest `display: standalone` or equivalent). Safari tabs on iPhone **cannot** use the Notifications API.

**Recommendation:** Add **standards-based Web Push** sent **directly from Django** via **`pywebpush`**, using **Declarative Web Push JSON** (`"web_push": 8030`) as the default payload so iOS 18.4+ can display notifications without relying on service-worker JavaScript, while a **minimal service worker** remains for iOS 16.4–18.3, desktop browsers, and optional `notificationclick` / mutable handling. **No new infrastructure** beyond outbound HTTPS to push endpoints (notably `*.push.apple.com`) and two new Railway secrets for **VAPID** keys.

**First independent milestone:** PWA install shell + authenticated subscribe/unsubscribe + “Send test notification” — **without** wiring new-mail events.

---

## 1. Repository findings (existing vs missing)

### 1.1 Frontend, auth, and mobile layout

| Area | Status | References |
|------|--------|------------|
| Templates | Server-rendered Django templates; base layout in `templates/base.html` | `viewport` meta present; **no** `theme-color`, **no** `apple-mobile-web-app-capable`, **no** touch icons |
| Styling | Single CSS file | `core/static/mailstead/app.css` — system font stack, sticky header, **768px breakpoint** with hamburger + off-canvas sidebar (`.nav-toggle`, `.mail-sidebar.is-open`) |
| JavaScript | Minimal inline scripts only | Folder nav toggle in `templates/mail/base_mail.html`; **no** build step, **no** npm frontend |
| Auth | Django session auth | `accounts/views.py` (`UserLoginView`), `LOGIN_URL` / redirects in `core/settings.py`; **no** explicit `SESSION_COOKIE_AGE` (Django default ~2 weeks) |
| HTMX | Installed | `django_htmx` middleware — suitable for small settings partials later, not required for push subscribe (needs user gesture + `fetch`) |
| Mobile UX | Usable responsive mail UI | Pagination (25/page), touch-friendly nav toggle; not marketed as installable app today |

**Missing for iPhone Home Screen:** `manifest.webmanifest`, icons (192/512 + `apple-touch-icon`), standalone display mode, service worker, push registration UI.

### 1.2 Manifest / service worker

**None exist.** Static assets are only `core/static/mailstead/app.css`. WhiteNoise serves compressed manifest static files (`CompressedManifestStaticFilesStorage`) — Django’s **static manifest**, not a **Web App Manifest**.

### 1.3 Email ingestion, filtering, delivery, background jobs

**Inbound path (existing):**

1. `POST /hooks/resend` → signature verify → `WebhookEvent` dedupe by `svix_id` → `enqueue("inbound", …, dedupe_key=f"inbound:{email_id}")` — `provider/webhooks.py`
2. Worker runs `mail.jobs.handle_inbound` → `ingest_inbound()` — `mail/inbound.py`
3. Idempotency: skip if `Message.resend_email_id` exists; webhook + job dedupe prevent double ingest
4. Recipients resolved; **filter rules** + DMARC fail → **Junk** folder — `mail/filtering.py`
5. Per mailbox: `MessageCopy` with `is_unread=True` (default), folder inbox/junk/sent/etc. — `mail/models.py`

**Other ingestion:** `reconcile_received` schedule every **15 min** pages Resend and enqueues missing IDs — `mail/reconcile.py`, `core/schedules.py`. Historical **`import_received`** management command uses a cursor — same enqueue pattern.

**Outbound:** Compose → `OutboundMessage` + send job; status webhooks update state — `mail/outbound.py`, `provider/webhooks.py`.

**Worker (existing):** `mailstead/run.py` supervises **gunicorn (1 worker, 4 threads)** + **one `manage.py worker`** process. Jobs: DB-backed queue with leases, exponential backoff, `dedupe_key` — `jobs/models.py`, `jobs/queue.py`. Handlers registered in `mail/jobs.py`, `provider/jobs.py`, `storage/jobs.py`.

**Proposed hook point (not implemented):** After successful `MessageCopy` creation for **new** inbound mail (inbox, not junk), enqueue a **`push_notify`** (or similar) job keyed by mailbox + debounce window — **must not** block ingest on push failures.

### 1.4 Notification / event models and user preferences

| Model / feature | Exists? | Notes |
|-----------------|---------|--------|
| `WebhookEvent` | Yes | Resend webhook audit, not user notifications |
| `UsageAlert` | Yes | Deduped threshold records — `provider/usage_service.py` |
| Usage alert **email** / in-app notice UI | **Partial / gap** | [ROADMAP.md](../ROADMAP.md) lists admin email + in-app notices; code only **creates `UsageAlert` rows** — no mail send on alert, minimal `/ops/resend-usage/` page |
| User notification preferences | **No** | No per-user opt-in, preview mode, or device list |
| Push subscriptions | **No** | — |

### 1.5 Deployment, origin, secrets

**Railway (existing):**

- Start: `python -m mailstead.run` — gunicorn + worker in one container — `docs/deploy-railway.md`, `Dockerfile`
- Volume: `/data` (SQLite default or optional Postgres via `DATABASE_URL`)
- Public URL: `PUBLIC_URL` or `https://$RAILWAY_PUBLIC_DOMAIN` — `core/settings.py`
- CSRF: `CSRF_TRUSTED_ORIGINS` derived from `PUBLIC_URL`
- Secrets today: `SECRET_KEY`, `APP_ENCRYPTION_KEY`, `BOOTSTRAP_TOKEN`, `RESEND_API_KEY`, optional `RESEND_WEBHOOK_SECRET`
- Cache: **database cache** (`mailstead_cache` table), not Redis

**Proposed secrets (addition):** `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` (or single JSON blob generated once at deploy). Stable across redeploys; rotation requires clients to resubscribe.

---

## 2. Platform support (official sources)

### 2.1 iOS Home Screen web app requirements

Sources: [Web Push for Web Apps on iOS and iPadOS (WebKit)](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/), [Sending web push notifications (Apple Developer)](https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers), [WebKit Features in Safari 16.4](https://webkit.org/blog/13966/webkit-features-in-safari-16-4/).

| Requirement | Detail |
|-------------|--------|
| Installation | User gesture: Share → **Add to Home Screen** (Safari since iOS 1; third-party browsers from **16.4** under entitlement rules) |
| Web app vs bookmark | Manifest `display`: **`standalone`** or **`fullscreen`** (or non-default display) → opens as web app; without it, icon is a bookmark opening in browser (**no push on iPhone in browser tab**) |
| Push APIs | Push API + Notifications API; **classic** path also requires **service worker** (`ServiceWorkerRegistration.pushManager`) on **16.4+** |
| Apple push endpoints | Subscriptions use **`https://*.push.apple.com`** — server egress must allow this |
| Developer program | **Not required** for Web Push on Apple platforms |
| macOS | Safari 16+ supports Web Push for **webpages in Safari** as well as installed web apps — lower priority for this proposal but same server code |

### 2.2 Permission and subscription flows

- Permission prompt must follow **direct user interaction** (tap on “Enable notifications”) — call `subscribe()` **synchronously from that click handler** (Apple docs).
- Subscriptions must use **`userVisibleOnly: true`** — no silent push on WebKit; silent handlers risk **permission revocation** on classic Web Push.
- User manages per-app notification settings in **Settings → Notifications** (same as native apps), including **Focus** modes (synced across devices when manifest `id` is used — WebKit 16.4+).
- **Badging API** (16.4+): badge permission tied to notification permission; declarative payloads can include **`app_badge`** — [Safari 16.4 WebKit blog](https://webkit.org/blog/13966/webkit-features-in-safari-16-4/).

### 2.3 Behavior when app is closed

Web Push on iOS uses **APNs** (same as native). Notifications appear on Lock Screen / Notification Center / Apple Watch per user settings. Delivery does **not** require the web app process to be running. **Background Sync / Periodic Background Sync** are separate, poorly supported on iOS for this use case — **do not rely on them for mail delivery**; treat push as the alert channel and **server/DB as source of truth**.

### 2.4 Notification click, login, session

- **Declarative Web Push** requires a **`navigate`** URL; browser opens it on tap **without service worker JS** — [Meet Declarative Web Push](https://webkit.org/blog/16535/meet-declarative-web-push/).
- Recommended navigate targets: `https://{PUBLIC_URL}/mail/m/{copy_id}/` or inbox with query — **must be same origin** as app.
- If session cookie expired: user sees **login page**; use `?next=/mail/m/123/` (Django `LOGIN_URL` redirect) — **no credentials in payload**.
- `SESSION_COOKIE_SECURE` is on in production; top-level navigation from notification should send cookies (`SameSite=Lax` default is OK for cross-context open from notification).

### 2.5 Limits, revocation, delivery

- **No silent push** on WebKit — every push must map to a visible notification (declarative JSON satisfies this on supported versions).
- **Classic Web Push:** if `push` event handler fails to call `showNotification` in time, WebKit may **revoke** push permission — mitigated by **Declarative Web Push** fallback content.
- **ITP / service worker eviction:** Safari may remove service worker registration after extended non-use; **Declarative Web Push (18.4+)** decouples display from SW; subscription via `window.pushManager` survives SW removal — [Meet Declarative Web Push](https://webkit.org/blog/16535/meet-declarative-web-push/).
- Push services may return **410 Gone** for expired subscriptions — treat as **delete local subscription row**.
- Exact APNs TTL / coalescing behavior for web push: **not fully documented in sources reviewed** — use modest TTL (e.g. 86400s) and idempotent dedupe on server.

### 2.6 Classic Web Push vs Declarative Web Push

| | Classic (16.4+) | Declarative (18.4+ Home Screen) |
|--|-----------------|----------------------------------|
| Subscribe | `registration.pushManager` (needs SW registered) | **`window.pushManager`** optional; shares subscription with SW if present |
| Payload | Opaque to SW; JS calls `showNotification` | JSON with `"web_push": 8030` + `notification` object |
| SW failure penalty | Can lose permission | **Fallback** shows declarative notification |
| pywebpush | Encrypt/send JSON string as today | Same — browser chooses declarative path |

**Recommended baseline:**

1. Ship **manifest + minimal SW** (push + optional `notificationclick` for non-declarative browsers).
2. Subscribe using feature detection: `window.pushManager ?? (await navigator.serviceWorker.ready).pushManager`.
3. Server always sends **declarative JSON**; SW `push` handler parses same JSON for Chrome/Firefox and older iOS.

**Feature detection (conceptual):**

```javascript
const canPush = ("PushManager" in window) || ("serviceWorker" in navigator);
const isStandalone = window.matchMedia("(display-mode: standalone)").matches
  || window.navigator.standalone === true;
// iPhone: surface "Add to Home Screen" instructions when !isStandalone
```

---

## 3. Smallest practical architecture

### 3.1 Components

```
[Resend webhook] → [inbound job] → ingest_inbound()
                                        ↓
                                 enqueue push_notify (debounced)
                                        ↓
[worker] → push_send job → pywebpush → *.push.apple.com / FCM / etc.
                ↑
[PushSubscription rows per device endpoint]
```

**No** Firebase, **no** OneSignal, **no** separate push microservice unless deliverability tooling is needed later.

### 3.2 Manifest responsibilities

- `name`, `short_name`, `start_url`: `/mail/` (or `/`)
- `display`: `standalone`
- `scope`: `/`
- `id`: stable URL (e.g. `PUBLIC_URL`) for Focus sync across devices
- `icons`: 192, 512 PNG (and list in manifest)
- `theme_color`, `background_color`: match `app.css`
- Link: `<link rel="manifest" href="{% url 'webmanifest' %}">` + Apple touch icon

Serve manifest from Django (dynamic `PUBLIC_URL`) or static with env at collectstatic — dynamic is simpler for multi-tenant Railway URLs.

### 3.3 Service worker responsibilities (minimal)

**Do:**

- `push` listener: parse declarative JSON; if not declarative-capable, `showNotification` + `clients.openWindow(navigate)`
- `notificationclick`: `event.notification.close(); clients.openWindow(navigate)` for browsers that need it
- `install` / `activate`: `skipWaiting()` only — **no precache of HTML**

**Do not:**

- Cache `/mail/*`, message bodies, or authenticated responses
- Implement generic offline mailbox — risk of **shared-device data leakage** on cached pages

Optional: cache-only ` /static/mailstead/*` with versioning via WhiteNoise hashed names — low value for push milestone.

### 3.4 Subscription registration and ownership

**New models (proposed):**

```python
class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=512)  # unique
    endpoint_hash = models.CharField(max_length=64, unique=True)  # SHA-256(endpoint)
    keys_json = models.JSONField()  # p256dh, auth
    user_agent = models.CharField(max_length=255, blank=True)
    label = models.CharField(max_length=64, blank=True)  # user-editable "Mahmoud's iPhone"
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=64, blank=True)

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_prefs")
    enabled = models.BooleanField(default=True)
    new_mail = models.BooleanField(default=True)
    sent_failures = models.BooleanField(default=True)
    preview_mode = models.CharField(max_length=16, default="private")  # private | subject | sender_subject
    quiet_hours_start = models.TimeField(null=True, blank=True)  # optional phase 2
    quiet_hours_end = models.TimeField(null=True, blank=True)
```

**Endpoints (proposed):**

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/notifications/settings/` | login | UI: status, devices, prefs, install help |
| POST | `/notifications/subscribe/` | login + CSRF | Body: PushSubscription JSON from browser |
| POST | `/notifications/unsubscribe/` | login + CSRF | Body: endpoint or id |
| POST | `/notifications/test/` | login + CSRF | Enqueue test push to current device |
| GET | `/manifest.webmanifest` | public | Manifest |
| GET | `/sw.js` | public | Service worker (`Service-Worker-Allowed: /`) |

**Registration rules:**

- Upsert by `endpoint_hash`; reassign `user` if same device logs in as different account (delete old row on user switch).
- On **logout**: optional JS `pushManager.getSubscription().unsubscribe()` + server DELETE — prevents next user on shared iPad receiving previous user’s mail alerts.
- **`invalidate_user_sessions`** exists — does not remove push subscriptions; consider admin “sign out everywhere” also marking subscriptions inactive.

### 3.5 VAPID and deployment

- Generate EC key pair once (e.g. `py-vapid` or `openssl`); store **private** key in Railway secret.
- Expose **public** key to template/JS as base64url (`VAPID_PUBLIC_KEY` env or derived endpoint `/notifications/vapid-public-key/`).
- `vapid_claims`: `{"sub": "mailto:ADMIN_RECOVERY_EMAIL"}` — reuse existing admin contact env.
- Document in `.env.example` and Railway template (generated secrets).

### 3.6 Worker integration

New job kinds:

- `push_send` — payload: `{subscription_id, payload_dict}` or `{user_id, event, ...}` resolved inside handler
- `push_notify_mailbox` — debounced: `{mailbox_id, reason}` → fan out to user’s active subscriptions

Use existing **`dedupe_key`** patterns:

- Debounce new mail: `push:mailbox:{mailbox_id}:pending` with `run_after=now+45s`, coalesce count in job payload or DB row `PendingPushBatch`
- Per-message dedupe: `push:copy:{copy_id}` once implemented

Handler calls `pywebpush.webpush(subscription_info, json.dumps(payload), vapid_private_key=..., vapid_claims=...)`.

**Retry:** inherit job `max_attempts` / backoff; **410/404** → mark subscription revoked, **complete** job (no retry). **429/5xx** → retry with backoff.

**Expiry / TTL:** pass `ttl` header via pywebpush where supported; stale notifications dropped by push service — acceptable for mail alerts.

### 3.7 Multiple devices, logout, revoked access

- Fan-out: N subscriptions per user; each send is independent.
- Disabled mailbox / user: skip enqueue at notify time; periodic cleanup optional.
- Staff-only admin alerts: separate preference flag `admin_ops` on staff users only.

### 3.8 When additional services help (optional, not recommended initially)

| Service | Benefit | Why skip at 10–50 users |
|---------|---------|-------------------------|
| Dedicated push broker (OneSignal, etc.) | Analytics, A/B | Extra vendor, cost, privacy |
| Redis queue | Faster job dispatch | DB queue already works |
| Separate worker service | Scale | Single container is enough |

---

## 4. Notification events and UX

### 4.1 When to notify

| Event | Audience | Default | Notes |
|-------|----------|---------|-------|
| New mail in **Inbox** | Mailbox owner | On | Skip **Junk**, **Sent** copies from inbound fan-out |
| New mail from **reconcile/import** | Same | **Off** or delayed | Pass `source: "reconcile"` in job; suppress unless copy `created_at` within last N minutes of notify job |
| **Duplicate webhook** | — | No double notify | Existing `inbound:{email_id}` dedupe |
| User already **read** message | — | Skip | At send time: `MessageCopy.is_unread` must still be `True` |
| **Burst** (many messages) | — | Coalesce | One notification: “5 new messages” → navigate to `/mail/?folder=inbox` |
| Outbound **bounced/failed** | Sender | On (pref) | Hook `apply_outbound_status` → enqueue user notify |
| **UsageAlert** / storage pressure | Staff | On | When `UsageAlert` created or ops thresholds — staff `NotificationPreference.admin_ops` |
| Delivery **delayed** | Optional | Off | Noisy; phase 2 |

**Filtering delay:** Junk assignment happens **before** `MessageCopy` insert — do not notify for junk folder.

**Independence from ingest:** Push failures must **never** fail `ingest_inbound`; wrap push in separate jobs with isolated exception handling.

### 4.2 Payload / privacy

**Default (private):**

```json
{
  "web_push": 8030,
  "notification": {
    "title": "New mail",
    "body": "You have a new message in Mailstead.",
    "navigate": "https://example.up.railway.app/mail/m/42/",
    "app_badge": "3"
  }
}
```

**Optional preview** (`preview_mode`): include truncated sender/subject in `body` — user opt-in on settings page.

Never put message body, attachments, or tokens in push payload.

### 4.3 User flows

1. **Install:** User visits site in Safari → Share → Add to Home Screen → open from icon (standalone).
2. **Log in:** Normal session cookie.
3. **Enable on this device:** Settings → Notifications → button “Enable on this device” → permission → POST subscribe.
4. **Test:** “Send test notification” → `push_send` job → verify Lock Screen.
5. **Manage:** List devices (endpoint labels, last seen), remove device, toggle prefs, preview mode.

**In-app copy for iPhone:** Explain that notifications **only work from the Home Screen app**, not from Safari tabs.

---

## 5. Security and operating limits

| Risk | Mitigation |
|------|------------|
| **SSRF via endpoint URL** | Allowlist host suffixes: `push.apple.com`, `updates.push.services.mozilla.com`, `fcm.googleapis.com`, `wns2-*.notify.windows.com`, etc. Reject private IP literals and non-HTTPS |
| **Subscription hijacking** | Subscribe endpoint requires authenticated session; bind row to `request.user`; CSRF token on POST |
| **Sensitive payloads** | Private default; no MIME in push |
| **Shared device** | Logout unsubscribes; manifest `id` + separate installs for work/personal (user responsibility) |
| **Secret handling** | VAPID private key only in env; never in repo |
| **SW cache leak** | No fetch handler for HTML/API |
| **Rate limits** | Cap test notifications (e.g. 3/hour/user); cap fan-out batch size; dead-letter after job max attempts |

### 5.1 Resource estimates (order of magnitude)

| Resource | Estimate | Uncertainty |
|----------|----------|-------------|
| DB | ~1–2 KB per subscription; negligible for &lt;100 devices | Low |
| Memory | pywebpush + HTTP per send; worker thread pool already 2 | Medium under burst |
| Network | One HTTPS POST per device per notification; Apple/FCM handle delivery | Low |
| Worker CPU | Coalescing reduces sends; reconcile without notify keeps load low | Medium |
| Maintenance | VAPID rotation, iOS behavior changes, allowlist updates | Ongoing low |

---

## 6. Implementation milestones

### M1 — Install shell + push plumbing (first milestone, independent)

- Web manifest + icons + meta tags
- Minimal `/sw.js` (push + notificationclick only)
- `PushSubscription` model + migrate
- VAPID settings + subscribe/unsubscribe/test endpoints
- Settings page with iOS install instructions
- `push_send` worker handler + unit tests (endpoint validation, payload builder)
- Railway docs: two new secrets, egress note for `*.push.apple.com`

**Exit criteria:** Real iPhone on Home Screen receives test notification; tap opens `/mail/` or settings URL while logged in.

### M2 — New mail notifications

- `push_notify_mailbox` debounce after inbox `MessageCopy` create
- Unread check + junk skip + import/reconcile suppression
- Coalesced title/body; badge count query (count unread inbox)

### M3 — Preferences and extra events

- `NotificationPreference` UI
- Outbound failure notifications
- Staff ops alerts tied to `UsageAlert` / ops dashboard signals

### M4 — Hardening

- Logout unsubscribe hook
- Subscription janitor (410 cleanup)
- Optional declarative-only path documentation for iOS 18.4+ testers

---

## 7. Automated checks (proposed)

**pytest (CI):**

- Endpoint allowlist rejects `http://169.254.169.254`, arbitrary domains
- Subscribe creates/updates row for authenticated user; rejects anonymous
- Payload builder: private vs preview modes; `navigate` uses `PUBLIC_URL`
- Job handler: 410 response marks `revoked_at`

**Not in CI (manual):**

- Real APNs delivery, Focus modes, badge on icon

---

## 8. Real iPhone acceptance checklist

- [ ] iOS **16.4+** device (note OS version)
- [ ] Site served over **HTTPS** with valid cert (`PUBLIC_URL`)
- [ ] Add to Home Screen; icon opens **standalone** (no Safari URL bar)
- [ ] `typeof Notification` is defined in standalone app
- [ ] Enable notifications from **button tap**; permission granted
- [ ] Test notification arrives with app **backgrounded**
- [ ] Test notification arrives with app **force-quit** (swiped away)
- [ ] Tap notification → correct message or inbox; login prompt if session cleared, then `next` works
- [ ] Junk mail does **not** notify (M2)
- [ ] Focus / Do Not Disturb respects user settings
- [ ] Revoke permission in Settings → app handles gracefully; re-enable works
- [ ] (Optional iOS **18.4+**) Verify delivery with SW disabled / after long idle (declarative path)

---

## 9. Official sources

1. [Web Push for Web Apps on iOS and iPadOS](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/) — installation, APNs endpoints, Focus, badging  
2. [Meet Declarative Web Push](https://webkit.org/blog/16535/meet-declarative-web-push/) — `web_push: 8030`, `window.pushManager`, navigate  
3. [WebKit Features in Safari 18.4](https://webkit.org/blog/16574/webkit-features-in-safari-18-4/) — declarative availability  
4. [Sending web push notifications in web apps and browsers (Apple)](https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers) — permission gesture, server setup, endpoint allowlisting  
5. [RFC 8030](https://www.rfc-editor.org/rfc/rfc8030) — Web Push protocol  
6. [pywebpush](https://github.com/web-push-libs/pywebpush) — Python sender  

---

## 10. Unresolved questions and assumptions

| Item | Assumption / question |
|------|------------------------|
| iOS version mix | Target **16.4+** with SW; treat **18.4+** declarative as enhancement |
| pywebpush + declarative | Assumed JSON body passes through unchanged; verify on first iPhone test |
| Usage alert email | [ROADMAP.md](../ROADMAP.md) — **not implemented**; ops push may duplicate future email work |
| Unread badge accuracy | Badge set at send time; may be stale if user reads on another device — acceptable for v1 |
| Quiet hours | Model sketched; implement in M3 if requested |
| Postgres vs SQLite | Push tables fine on both; same worker |
| Multi-mailbox users | Current model: **one mailbox per user** — fan-out is per user, not per alias |

---

## 11. Tradeoffs summary

| Choice | Pros | Cons |
|--------|------|------|
| Direct pywebpush from worker | No new infra; fits Railway single container | Must maintain endpoint allowlist; push latency tied to worker |
| Declarative-first payload | iOS 18.4+ reliability; simpler SW | Older iOS still needs SW handler |
| Debounced coalescing | Fewer notifications; less battery | Slight delay (30–60 s) |
| Private default body | Privacy on lock screen | Less context until open |
| No offline mail cache | Security | No offline reading |

---

**Concrete first milestone:** Implement **§6 M1** only — manifest, minimal service worker, VAPID env vars, `PushSubscription` + subscribe/unsubscribe/test API, settings UI with iPhone install guidance, and worker-delivered test push — **without** connecting to inbound mail events.
