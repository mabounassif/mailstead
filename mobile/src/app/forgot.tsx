import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Button, Notice, TextField } from "@/components/ui";
import { api } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function ForgotScreen() {
  const [username, setUsername] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit() {
    setBusy(true);
    setError(null);
    try {
      await api("/api/v1/auth/password-reset/", {
        method: "POST",
        auth: false,
        body: { username: username.trim() },
      });
      setDone(true);
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.body}>
      {done ? (
        <>
          <Notice text="Check the recovery email for a reset link. Open the Mailstead app link on this phone." tone="info" />
          <Button label="Back to sign in" onPress={() => router.replace("/login")} tone="quiet" />
        </>
      ) : (
        <>
          <TextField
            label="Username"
            autoCapitalize="none"
            autoCorrect={false}
            value={username}
            onChangeText={setUsername}
            editable={!busy}
          />
          {error ? <Notice text={error} /> : null}
          <Button label={busy ? "Sending…" : "Send reset link"} onPress={() => void onSubmit()} disabled={busy} />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  body: { flex: 1, backgroundColor: colors.bg, padding: 20, gap: 14 },
});
