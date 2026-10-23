# Mobile companion (Expo)

Optional native iOS/Android shell for a self-hosted Mailstead instance. Source and
release steps live in [`mobile/`](../mobile/README.md).

## Status

| Claim | Reality |
| --- | --- |
| Native store binaries via EAS | Supported once you link Expo + Apple/Google accounts |
| Product UI | Unchanged Django / HTMX app loaded in a WebView at your `PUBLIC_URL` |
| Separate mobile REST API | **Not implemented** — not required for this shell |
| Required for self-hosting | **No** — Docker web deploy remains standalone |

This does not replace the server-rendered UI and is not a native rewrite of
Messages / Drive / Contacts / Settings.

## Quick path to a store build

1. Deploy Mailstead with HTTPS `PUBLIC_URL` (see [deploy](deploy-railway.md)).
2. Follow [mobile/README.md](../mobile/README.md): `eas init`, replace icons,
   build with the `production` profile, submit with the `production` submit
   profile.
3. Complete App Store / Play Console listing, privacy policy, and data-safety
   forms (session cookies for the user’s host).

Apple Developer and Google Play memberships, and Expo account linking, are
operator steps outside this repository.
