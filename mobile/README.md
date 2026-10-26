# Mailstead mobile (Expo)

Optional native client for a self-hosted Mailstead instance. Messages, Drive,
Contacts, Settings, and a local review queue run in the app. Mail talks to
`/api/v1/` on your server. Review requests are sample data on the device.
The Django site remains the desktop product.

Sign-in uses your existing username and password. The app stores a bearer token
on the device. There is no Mailstead-hosted multi-tenant backend: each person
points the app at their own instance.

Formatted email HTML renders in a sandboxed WebView with JavaScript disabled.
Everything else is native.

## Local development

```bash
cd mobile
cp .env.example .env.local   # optional EXPO_PUBLIC_MAILSTEAD_URL
npm install
npm run start
```

Then open Expo Go (SDK 58) or a development build. On the setup screen, enter
the same public URL as your Mailstead host (HTTPS in release builds; `http://`
is allowed only in `__DEV__` for local servers). Sign in with a mailbox user
from that server.

```bash
npm run typecheck
npm test
```

Native push registration needs an EAS project id (`eas init`) and a development
or store build. Expo Go on Android cannot obtain a remote push token. The server
delivers those tokens only when `EXPO_ACCESS_TOKEN` is set. Without it, notification
preferences still save and Web Push is unchanged.

## Release checklist (App Store / Play Store)

These steps require **your** Expo, Apple Developer, and Google Play accounts.
This repo does not create those accounts or spend money on your behalf.

1. **Expo project**
   ```bash
   cd mobile
   npx eas-cli@latest login
   npx eas-cli@latest init   # writes projectId into app config / EAS
   ```
   Set `EAS_PROJECT_ID` (and optionally `EXPO_OWNER`) in EAS secrets or `.env.local`
   if you keep `projectId` out of git.

2. **Identifiers** — already set in `app.config.ts`:
   - iOS bundle / Android package: `app.mailstead.mobile`
   - Scheme: `mailstead`
   Change them before the first store listing if you need a different identity;
   they are hard to rename after publication.

3. **Icons & splash** — replace files under `assets/` with final brand art
   (1024×1024 icon, adaptive Android layers). Current files are Expo placeholders.

4. **Privacy & store listing**
   - Host a privacy policy URL (bearer token for the user’s Mailstead host;
     no third-party analytics in this app).
   - Prepare screenshots for phone (and tablet if you keep `supportsTablet`).
   - Complete Apple privacy nutrition labels and Google Data safety forms
     (account credentials and mailbox content on the user's host).

5. **Credentials**
   - Apple Developer Program membership for iOS store builds.
   - Google Play Developer account for Play uploads.
   - Let EAS manage signing (`credentialsSource: remote`, the default) unless
     you have an existing keystore / distribution cert.
   - For push, configure Expo push credentials and set `EXPO_ACCESS_TOKEN` on
     the Mailstead server. The app still ships if you skip this.

6. **Build**
   ```bash
   npm run eas:build:preview      # internal APK / ad-hoc style testing
   npm run eas:build:production   # store AAB + iOS IPA
   ```

7. **Submit**
   ```bash
   # After production builds finish and store apps exist:
   npx eas-cli@latest submit --profile production --platform android
   npx eas-cli@latest submit --profile production --platform ios
   ```
   Fill `submit.production.ios` in `eas.json` with `ascAppId` / team details
   once App Store Connect has the app record. Android submit uses a Google
   service account JSON linked in EAS or `serviceAccountKeyPath`.

8. **Point the binary at your host**
   - Leave `EXPO_PUBLIC_MAILSTEAD_URL` empty so each user types their instance, or
   - Set it for a single-tenant branded build of one deployment.

## What this is / is not

| Is | Is not |
| --- | --- |
| Native Messages, Drive, Contacts, and Settings | A replacement for the Django website |
| `/api/v1/` on your existing Mailstead server | A Mailstead-hosted multi-tenant mobile backend |
| Optional; Docker web deploy stays standalone | Required for self-hosting |

Password reset emails include both the website link and a `mailstead://` link
that opens the new-password screen. Django admin, ops, and first-time bootstrap
setup stay in the browser.
