import type { ExpoConfig, ConfigContext } from "expo/config";

const APP_NAME = "Mailstead";
const SLUG = "mailstead";
const BUNDLE_ID = "app.mailstead.mobile";
const SCHEME = "mailstead";

/**
 * Optional default instance URL baked into a branded build.
 * Users can still change it in-app. Prefer HTTPS for store builds.
 */
const defaultInstanceUrl = process.env.EXPO_PUBLIC_MAILSTEAD_URL?.trim() || "";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: APP_NAME,
  slug: SLUG,
  version: "1.0.0",
  orientation: "portrait",
  icon: "./assets/icon.png",
  scheme: SCHEME,
  userInterfaceStyle: "light",
  ios: {
    supportsTablet: true,
    bundleIdentifier: BUNDLE_ID,
    buildNumber: "1",
    infoPlist: {
      // Bearer token for the user's Mailstead host; no encryption beyond TLS.
      ITSAppUsesNonExemptEncryption: false,
      NSAppTransportSecurity: {
        NSAllowsArbitraryLoads: false,
      },
    },
    config: {
      usesNonExemptEncryption: false,
    },
  },
  android: {
    package: BUNDLE_ID,
    versionCode: 1,
    adaptiveIcon: {
      backgroundColor: "#f6f8fc",
      foregroundImage: "./assets/android-icon-foreground.png",
      backgroundImage: "./assets/android-icon-background.png",
      monochromeImage: "./assets/android-icon-monochrome.png",
    },
    predictiveBackGestureEnabled: false,
    permissions: ["INTERNET", "ACCESS_NETWORK_STATE", "POST_NOTIFICATIONS"],
  },
  web: {
    favicon: "./assets/favicon.png",
  },
  plugins: [
    "expo-router",
    [
      "expo-splash-screen",
      {
        backgroundColor: "#f6f8fc",
        image: "./assets/splash-icon.png",
        imageWidth: 200,
      },
    ],
    "expo-system-ui",
    "expo-secure-store",
    [
      "expo-notifications",
      {
        color: "#1a73e8",
      },
    ],
  ],
  experiments: {
    typedRoutes: true,
  },
  extra: {
    defaultInstanceUrl,
    eas: {
      // Set by `npx eas-cli init` / linked Expo project — do not invent an ID.
      projectId: process.env.EAS_PROJECT_ID,
    },
  },
  owner: process.env.EXPO_OWNER,
});
