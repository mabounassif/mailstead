import { useCallback, useEffect, useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { Button, Empty, ListRow, Loading, Notice, TextField } from "@/components/ui";
import { api, type Card } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function WalletsScreen() {
  const [cards, setCards] = useState<Card[] | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const response = await api<{ cards: Card[] }>("/api/v1/cards/");
      setCards(response.cards);
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
      await api("/api/v1/cards/", { method: "POST", body: { title: title.trim(), body } });
      setTitle("");
      setBody("");
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(card: Card) {
    try {
      await api(`/api/v1/cards/${card.id}/`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }

  if (!cards && !error) {
    return <Loading />;
  }

  return (
    <FlatList
      style={styles.flex}
      data={cards ?? []}
      keyExtractor={(item) => String(item.id)}
      ListHeaderComponent={
        <View style={styles.form}>
          {error ? <Notice text={error} /> : null}
          <TextField label="Title" value={title} onChangeText={setTitle} />
          <TextField label="Note" value={body} onChangeText={setBody} multiline style={styles.note} />
          <Button label={busy ? "Saving…" : "Add card"} onPress={() => void onCreate()} disabled={busy} />
        </View>
      }
      ListEmptyComponent={<Empty title="No cards yet" />}
      renderItem={({ item }) => (
        <ListRow title={item.title} subtitle={item.body ? `${item.body}\nTap to delete` : "Tap to delete"} onPress={() => void onDelete(item)} />
      )}
    />
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  form: { padding: 16, gap: 12 },
  note: { minHeight: 80, textAlignVertical: "top" },
});
