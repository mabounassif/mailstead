import { router } from "expo-router";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ComponentRef,
  type ComponentType,
} from "react";
import {
  ActivityIndicator,
  BackHandler,
  Linking,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  WebView as RNWebView,
  type WebViewNavigation,
  type WebViewProps,
} from "react-native-webview";
import {
  clearInstanceUrl,
  loadSavedInstanceUrl,
  sameOrigin,
} from "@/lib/instanceUrl";
import { colors } from "@/theme";

// react-native-webview@14 collapses JSX props to `never` when the generic
// defaults to `undefined` (fixed upstream in 16.x; Expo 58 pins 14.0.1).
const WebView = RNWebView as unknown as ComponentType<WebViewProps>;
type WebViewHandle = ComponentRef<typeof RNWebView>;

export default function SessionScreen() {
  const webRef = useRef<WebViewHandle>(null);
  const [instanceUrl, setInstanceUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [canGoBack, setCanGoBack] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const url = await loadSavedInstanceUrl();
      if (cancelled) {
        return;
      }
      if (!url) {
        router.replace("/setup");
        return;
      }
      setInstanceUrl(url);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (Platform.OS !== "android") {
      return;
    }
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      if (canGoBack && webRef.current) {
        webRef.current.goBack();
        return true;
      }
      return false;
    });
    return () => sub.remove();
  }, [canGoBack]);

  const onNavChange = useCallback((nav: WebViewNavigation) => {
    setCanGoBack(nav.canGoBack);
  }, []);

  const onShouldStart = useCallback(
    (request: { url: string; isTopFrame?: boolean }) => {
      if (!instanceUrl) {
        return false;
      }
      const { url } = request;
      if (
        url.startsWith("about:") ||
        url.startsWith("blob:") ||
        url.startsWith("data:")
      ) {
        return true;
      }
      if (sameOrigin(url, instanceUrl)) {
        return true;
      }
      void Linking.openURL(url);
      return false;
    },
    [instanceUrl],
  );

  async function onChangeInstance() {
    await clearInstanceUrl();
    router.replace("/setup");
  }

  if (!instanceUrl) {
    return (
      <View style={styles.boot}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={["top", "left", "right"]}>
      <View style={styles.toolbar}>
        <Text style={styles.host} numberOfLines={1}>
          {instanceUrl.replace(/^https?:\/\//, "")}
        </Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Change Mailstead instance"
          onPress={onChangeInstance}
          hitSlop={8}
        >
          <Text style={styles.change}>Change</Text>
        </Pressable>
      </View>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Could not load Mailstead</Text>
          <Text style={styles.errorBody}>{error}</Text>
          <Pressable
            accessibilityRole="button"
            onPress={() => {
              setError(null);
              setLoading(true);
              webRef.current?.reload();
            }}
            style={styles.retry}
          >
            <Text style={styles.retryText}>Retry</Text>
          </Pressable>
        </View>
      ) : null}

      <View style={styles.webWrap}>
        {loading ? (
          <View style={styles.loadingOverlay} pointerEvents="none">
            <ActivityIndicator color={colors.accent} />
          </View>
        ) : null}
        <WebView
          // ComponentType drops ref typing; keep imperative handle for back/reload.
          {...({ ref: webRef } as object)}
          source={{ uri: instanceUrl }}
          style={styles.web}
          onLoadStart={() => {
            setLoading(true);
            setError(null);
          }}
          onLoadEnd={() => setLoading(false)}
          onNavigationStateChange={onNavChange}
          onShouldStartLoadWithRequest={onShouldStart}
          onError={(event) => {
            setLoading(false);
            setError(event.nativeEvent.description || "Network error");
          }}
          onHttpError={(event) => {
            if (event.nativeEvent.statusCode >= 500) {
              setError(`Server error (${event.nativeEvent.statusCode})`);
            }
          }}
          sharedCookiesEnabled
          thirdPartyCookiesEnabled
          domStorageEnabled
          allowsBackForwardNavigationGestures
          startInLoadingState={false}
          setSupportMultipleWindows={false}
          applicationNameForUserAgent="MailsteadMobile/1.0"
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  boot: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bg,
  },
  toolbar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    backgroundColor: colors.bg,
  },
  host: {
    flex: 1,
    fontSize: 14,
    fontWeight: "600",
    color: colors.text,
  },
  change: {
    fontSize: 14,
    fontWeight: "600",
    color: colors.accent,
  },
  webWrap: {
    flex: 1,
    position: "relative",
  },
  web: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFill,
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1,
  },
  errorBox: {
    padding: 16,
    gap: 8,
    backgroundColor: colors.surface,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
  },
  errorBody: {
    fontSize: 14,
    color: colors.muted,
  },
  retry: {
    alignSelf: "flex-start",
    marginTop: 4,
    backgroundColor: colors.accent,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  retryText: {
    color: "#ffffff",
    fontWeight: "600",
  },
});
