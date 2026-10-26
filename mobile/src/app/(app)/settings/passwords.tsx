import { useCallback, useEffect, useState } from "react";
import { FlatList, StyleSheet, Text, View } from "react-native";
import { Button, Empty, Loading, Notice, TextField } from "@/components/ui";
import { api, type VaultEntry } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function PasswordsScreen() {
  const [entries, setEntries] = useState<VaultEntry[] | null>(null);
  const [label, setLabel] = useState("");
  const [username, setUsername] = useState("");
  const [secret, setSecret] = useState("");
  const [revealed, setRevealed] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const response = await api<{ entries: VaultEntry[] }>("/api/v1/vault/");
      setEntries(response.entries);
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate() {
    setBusy(true);
    setError(null);
    try {
      await api("/api/v1/vault/", {
        method: "POST",
        body: { label: label.trim(), username: username.trim(), secret },
      });
      setLabel("");
      setUsername("");
      setSecret("");
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onReveal(entry: VaultEntry) {
    try {
      const result = await api<{ secret: string }>(`/api/v1/vault/${entry.id}/reveal/`, { method: "POST" });
      setRevealed((current) => ({ ...current, [entry.id]: result.secret }));
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }

  async function onDelete(entry: VaultEntry) {
    try {
      await api(`/api/v1/vault/${entry.id}/`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }

  if (!entries && !error) {
    return <Loading />;
  }

  return (
    <FlatList
      style={styles.flex}
      data={entries ?? []}
      keyExtractor={(item) => String(item.id)}
      ListHeaderComponent={
        <View style={styles.form}>
          {error ? <Notice text={error} /> : null}
          <TextField label="Name" value={label} onChangeText={setLabel} />
          <TextField label="Username" autoCapitalize="none" value={username} onChangeText={setUsername} />
          <TextField label="Secret" secureTextEntry value={secret} onChangeText={setSecret} />
          <Button label={busy ? "Saving…" : "Add password"} onPress={() => void onCreate()} disabled={busy} />
        </View>
      }
      ListEmptyComponent={<Empty title="No passwords yet" />}
      renderItem={({ item }) => (
        <View style={styles.entry}>
          <Text style={styles.name}>{item.label}</Text>
          {item.username ? <Text style={styles.meta}>{item.username}</Text> : null}
          {revealed[item.id] !== undefined ? <Text style={styles.secret}>{revealed[item.id]}</Text> : null}
          <View style={styles.actions}>
            <Button label="Reveal" tone="quiet" onPress={() => void onReveal(item)} />
            <Button label="Delete" tone="danger" onPress={() => void onDelete(item)} />
          </View>
        </View>
      )}
    />
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  form: { padding: 16, gap: 12 },
  entry: { padding: 16, gap: 8, borderBottomColor: colors.border, borderBottomWidth: StyleSheet.hairlineWidth },
  name: { color: colors.text, fontSize: 16, fontWeight: "600" },
  meta: { color: colors.muted, fontSize: 14 },
  secret: { color: colors.text, fontSize: 16 },
  actions: { flexDirection: "row", gap: 8 },
});
