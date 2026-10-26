import { Link, router } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Button, Notice, TextField } from "@/components/ui";
import { api } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { clearInstanceUrl } from "@/lib/instanceUrl";
import { clearToken, saveToken } from "@/lib/session";
import { colors } from "@/theme";

export default function LoginScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSignIn() {
    setBusy(true);
    setError(null);
    try {
      const result = await api<{ token: string }>("/api/v1/auth/login/", {
        method: "POST",
        auth: false,
        body: { username: username.trim(), password },
      });
      await saveToken(result.token);
      router.replace("/(app)/messages");
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onChangeInstance() {
    await clearToken();
    await clearInstanceUrl();
    router.replace("/setup");
  }

  return (
    <SafeAreaView style={styles.safe} edges={["bottom", "left", "right"]}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={styles.body}>
          <TextField
            label="Username"
            autoCapitalize="none"
            autoCorrect={false}
            value={username}
            onChangeText={setUsername}
            editable={!busy}
          />
          <TextField
            label="Password"
            secureTextEntry
            value={password}
            onChangeText={setPassword}
            editable={!busy}
            onSubmitEditing={() => void onSignIn()}
          />
          {error ? <Notice text={error} /> : null}
          <Button label={busy ? "Signing in…" : "Sign in"} onPress={() => void onSignIn()} disabled={busy} />
          <Link href="/forgot" style={styles.link}>
            Forgot password
          </Link>
          <Text style={styles.link} onPress={() => void onChangeInstance()}>
            Use a different server
          </Text>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  body: { flex: 1, padding: 20, gap: 14 },
  link: { color: colors.accent, fontSize: 16, textAlign: "center" },
});
