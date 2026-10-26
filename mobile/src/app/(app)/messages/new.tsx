import { router } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet } from "react-native";
import { Button, Notice, TextField } from "@/components/ui";
import { api, type SendResult } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function NewMessageScreen() {
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSend() {
    setBusy(true);
    setError(null);
    try {
      const result = await api<SendResult>("/api/v1/conversations/", {
        method: "POST",
        body: {
          to: to.split(",").map((part) => part.trim()).filter(Boolean),
          subject: subject.trim(),
          body,
        },
      });
      if (result.dm_key) {
        router.replace({ pathname: "/(app)/messages/thread", params: { dm: result.dm_key } });
      } else if (result.conversation_id) {
        router.replace({
          pathname: "/(app)/messages/thread",
          params: { channel: String(result.conversation_id) },
        });
      } else {
        router.back();
      }
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
        <TextField label="To" autoCapitalize="none" autoCorrect={false} value={to} onChangeText={setTo} placeholder="name@example.com" />
        <TextField label="Subject" value={subject} onChangeText={setSubject} placeholder="Optional for a direct message" />
        <TextField
          label="Message"
          value={body}
          onChangeText={setBody}
          multiline
          style={styles.message}
        />
        {error ? <Notice text={error} /> : null}
        <Button label={busy ? "Sending…" : "Send"} onPress={() => void onSend()} disabled={busy} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  body: { padding: 16, gap: 14 },
  message: { minHeight: 120, textAlignVertical: "top" },
});
