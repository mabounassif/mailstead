import { router } from "expo-router";
import { useState } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { Empty, ListRow, Notice, TextField } from "@/components/ui";
import { api, type CopySummary, type Page } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function SearchScreen() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CopySummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function onSearch() {
    setError(null);
    try {
      const page = await api<Page<CopySummary>>(`/api/v1/search/?q=${encodeURIComponent(query.trim())}`);
      setResults(page.results);
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }

  return (
    <View style={styles.flex}>
      <View style={styles.search}>
        <TextField
          label="Search"
          value={query}
          onChangeText={setQuery}
          autoCapitalize="none"
          returnKeyType="search"
          onSubmitEditing={() => void onSearch()}
        />
      </View>
      {error ? <Notice text={error} /> : null}
      <FlatList
        data={results}
        keyExtractor={(item) => String(item.copy_id)}
        ListEmptyComponent={<Empty title="No matches" hint="Search subject, sender, or message text." />}
        renderItem={({ item }) => (
          <ListRow
            title={item.subject || "(no subject)"}
            subtitle={`${item.from} · ${item.snippet}`}
            unread={item.unread}
            onPress={() =>
              router.push({ pathname: "/(app)/messages/copy/[copyId]", params: { copyId: String(item.copy_id) } })
            }
          />
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  search: { padding: 16 },
});
