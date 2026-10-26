import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Button, Notice, TextField } from "@/components/ui";
import { api } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function ResetConfirmScreen() {
  const params = useLocalSearchParams<{ uid: string; token: string }>();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit() {
    setBusy(true);
    setError(null);
    try {
      await api("/api/v1/auth/password-reset/confirm/", {
        method: "POST",
        auth: false,
        body: {
          uid: params.uid,
          token: params.token,
          password,
          password_confirm: confirm,
        },
      });
      router.replace("/login");
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.body}>
      <TextField label="New password" secureTextEntry value={password} onChangeText={setPassword} editable={!busy} />
      <TextField
        label="Confirm password"
        secureTextEntry
        value={confirm}
        onChangeText={setConfirm}
        editable={!busy}
      />
      {error ? <Notice text={error} /> : null}
      <Button label={busy ? "Saving…" : "Save password"} onPress={() => void onSubmit()} disabled={busy} />
    </View>
  );
}

const styles = StyleSheet.create({
  body: { flex: 1, backgroundColor: colors.bg, padding: 20, gap: 14 },
});
