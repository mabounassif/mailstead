import { useState, type ComponentType } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { WebView as RNWebView, type WebViewProps } from "react-native-webview";
import { colors } from "@/theme";

const WebView = RNWebView as unknown as ComponentType<WebViewProps>;

export function HtmlMail({ html, onLoadImages }: { html: string; onLoadImages?: () => void }) {
  const [blockedNavigation, setBlockedNavigation] = useState(false);
  if (!html) {
    return null;
  }
  return (
    <View style={styles.wrap}>
      <WebView
        originWhitelist={["*"]}
        source={{ html }}
        style={styles.web}
        javaScriptEnabled={false}
        setSupportMultipleWindows={false}
        onShouldStartLoadWithRequest={(request) => {
          if (request.navigationType === "click") {
            setBlockedNavigation(true);
            return false;
          }
          return true;
        }}
      />
      {onLoadImages ? (
        <Pressable accessibilityRole="button" onPress={onLoadImages} style={styles.load}>
          <Text style={styles.loadText}>Load images</Text>
        </Pressable>
      ) : null}
      {blockedNavigation ? <Text style={styles.note}>Links in messages stay in the message.</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: colors.surface },
  web: { flex: 1, backgroundColor: colors.surface },
  load: { padding: 12 },
  loadText: { color: colors.accent, fontSize: 15 },
  note: { color: colors.muted, fontSize: 13, paddingHorizontal: 12, paddingBottom: 8 },
});
