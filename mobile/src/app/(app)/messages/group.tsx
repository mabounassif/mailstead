import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, View } from "react-native";
import { Button, Notice, TextField } from "@/components/ui";
import { api } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function NewGroupScreen() {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onCreate() {
    setBusy(true);
    setError(null);
    try {
      const project = await api<{ id: number }>("/api/v1/projects/", {
        method: "POST",
        body: { name: name.trim() },
      });
      router.replace({ pathname: "/(app)/messages/thread", params: { project: String(project.id) } });
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <View style={styles.body}>
      <TextField label="Name" value={name} onChangeText={setName} editable={!busy} />
      {error ? <Notice text={error} /> : null}
      <Button label={busy ? "Creating…" : "Create group"} onPress={() => void onCreate()} disabled={busy} />
    </View>
  );
}

const styles = StyleSheet.create({
  body: { flex: 1, backgroundColor: colors.bg, padding: 16, gap: 14 },
});
