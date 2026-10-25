import { router } from "expo-router";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import {
  getBakedDefaultUrl,
  normalizeInstanceUrl,
  saveInstanceUrl,
} from "@/lib/instanceUrl";
import { colors } from "@/theme";

export default function SetupScreen() {
  const [value, setValue] = useState(getBakedDefaultUrl());
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function onConnect() {
    setError(null);
    const normalized = normalizeInstanceUrl(value);
    if (!normalized) {
      setError(
        __DEV__
          ? "Enter a valid http(s) URL for your Mailstead host."
          : "Enter a valid https URL for your Mailstead host.",
      );
      return;
    }
    setSaving(true);
    try {
      await saveInstanceUrl(normalized.origin);
      router.replace("/session");
    } catch {
      setError("Could not save the instance URL. Try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe} edges={["bottom", "left", "right"]}>
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <View style={styles.body}>
          <Text style={styles.brand}>Mailstead</Text>
          <Text style={styles.lead}>
            Open your self-hosted Mailstead in a native shell. Sign-in and mail
            stay on your server — this app does not add a separate account or
            API.
          </Text>

          <Text style={styles.label}>Instance URL</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete="url"
            keyboardType="url"
            placeholder="https://mail.example.com"
            placeholderTextColor={colors.muted}
            value={value}
            onChangeText={setValue}
            style={styles.input}
            editable={!saving}
            onSubmitEditing={onConnect}
            returnKeyType="go"
          />
          {error ? <Text style={styles.error}>{error}</Text> : null}

          <Pressable
            accessibilityRole="button"
            disabled={saving}
            onPress={onConnect}
            style={({ pressed }) => [
              styles.cta,
              (pressed || saving) && styles.ctaPressed,
            ]}
          >
            <Text style={styles.ctaText}>
              {saving ? "Connecting…" : "Connect"}
            </Text>
          </Pressable>

          <Text style={styles.note}>
            Use the same public URL as your deployment (`PUBLIC_URL`). Store
            builds require HTTPS.
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  flex: {
    flex: 1,
  },
  body: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 12,
    gap: 12,
  },
  brand: {
    fontSize: 34,
    fontWeight: "700",
    color: colors.text,
    letterSpacing: -0.5,
  },
  lead: {
    fontSize: 16,
    lineHeight: 24,
    color: colors.muted,
    marginBottom: 12,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.muted,
    textTransform: "uppercase",
    letterSpacing: 0.4,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === "ios" ? 14 : 12,
    fontSize: 16,
    color: colors.text,
  },
  error: {
    color: colors.danger,
    fontSize: 14,
  },
  cta: {
    marginTop: 8,
    backgroundColor: colors.accent,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  ctaPressed: {
    backgroundColor: colors.accentHover,
    opacity: 0.95,
  },
  ctaText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "600",
  },
  note: {
    marginTop: 8,
    fontSize: 13,
    lineHeight: 19,
    color: colors.muted,
  },
});
