# Mailstead mobile (Expo)

Optional native shell for a self-hosted Mailstead instance. The Django / HTMX
app remains the product UI; this package wraps your `PUBLIC_URL` in an Expo
WebView so you can distribute iOS and Android builds via EAS.

There is **no separate mobile API** in this repository. Session login, mail, and
settings run on your existing deployment.

## Local development

```bash
cd mobile
cp .env.example .env.local   # optional EXPO_PUBLIC_MAILSTEAD_URL
npm install
npm run start
```

Then open Expo Go (SDK 58) or a development build. On the setup screen, enter
the same public URL as your Mailstead host (HTTPS in release builds; `http://`
is allowed only in `__DEV__` for local servers).

```bash
npm run typecheck
npm test
```

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
   - Host a privacy policy URL (session cookies for the user’s Mailstead host;
     no third-party analytics in this shell).
   - Prepare screenshots for phone (and tablet if you keep `supportsTablet`).
   - Complete Apple privacy nutrition labels and Google Data safety forms
     (web content / cookies).

5. **Credentials**
   - Apple Developer Program membership for iOS store builds.
   - Google Play Developer account for Play uploads.
   - Let EAS manage signing (`credentialsSource: remote`, the default) unless
     you have an existing keystore / distribution cert.

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
| Release-ready Expo + EAS project | A native rewrite of Messages / Drive / Contacts |
| WebView of your Mailstead `PUBLIC_URL` | A Mailstead-hosted multi-tenant mobile backend |
| Optional; Docker web deploy stays standalone | Required for self-hosting |

A future native client would need authenticated versioned HTTP APIs on the
server — out of scope for this slice and not implied by shipping this shell.
