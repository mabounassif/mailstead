# Mobile companion (Expo)

Optional native iOS/Android client for a self-hosted Mailstead instance. Source and
release steps live in [`mobile/`](../mobile/README.md).

The phone app signs in to your server and uses `/api/v1/`. Messages, Drive,
Contacts, and Settings are React Native screens. The Django site stays the
desktop product and is still what a browser opens. Formatted email HTML is shown
in a sandboxed WebView with JavaScript disabled. Remote images stay blocked
until the reader asks to load them.

## Status

| Claim | Reality |
| --- | --- |
| Native store binaries via EAS | Supported once you link Expo + Apple/Google accounts |
| Phone UI | Native screens for Messages, Drive, Contacts, Settings, and a local sample review queue |
| Mailbox API | `/api/v1/` bearer tokens, scoped to the signed-in mailbox |
| Required for self-hosting | **No** — Docker web deploy remains standalone |
| Native push | Optional. Needs `EXPO_ACCESS_TOKEN` plus the operator's Expo/Apple/Google push credentials. Web Push is unchanged when that token is absent |

Django admin, the staff ops dashboard, and the one-time bootstrap setup URL stay
on the website. Sent, drafts, and archive do not have their own screens.

## Quick path to a store build

1. Deploy Mailstead with HTTPS `PUBLIC_URL` (see [deploy](deploy-railway.md)).
2. Follow [mobile/README.md](../mobile/README.md): `eas init`, replace icons,
   build with the `production` profile, submit with the `production` submit
   profile.
3. Set `EXPO_ACCESS_TOKEN` on the server if this build should receive push.
   Leave it empty and the app still works; it reports that push is not configured.
4. Complete App Store / Play Console listing, privacy policy, and data-safety
   forms (the app stores a bearer token for the user's host).

Apple Developer and Google Play memberships, and Expo account linking, are
operator steps outside this repository.
