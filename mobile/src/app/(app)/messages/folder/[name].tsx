import { router, useLocalSearchParams, useNavigation } from "expo-router";
import { useCallback, useLayoutEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { Button, Empty, ListRow, Loading, Notice } from "@/components/ui";
import { api, type CopySummary, type Page } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function FolderScreen() {
  const { name } = useLocalSearchParams<{ name: string }>();
  const folder = name === "trash" ? "trash" : "junk";
  const navigation = useNavigation();
  const [page, setPage] = useState<Page<CopySummary> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPage(await api<Page<CopySummary>>(`/api/v1/folders/${folder}/`));
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setRefreshing(false);
    }
  }, [folder]);

  useLayoutEffect(() => {
    navigation.setOptions({ title: folder === "trash" ? "Trash" : "Junk" });
    void load();
  }, [folder, load, navigation]);

  async function onEmpty() {
    try {
      await api("/api/v1/trash/empty/", { method: "POST" });
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }

  if (!page && !error) {
    return <Loading />;
  }

  return (
    <View style={styles.flex}>
      {error ? <Notice text={error} /> : null}
      {folder === "trash" ? (
        <View style={styles.emptyAction}>
          <Button label="Empty trash" tone="danger" onPress={() => void onEmpty()} />
        </View>
      ) : null}
      <FlatList
        data={page?.results ?? []}
        keyExtractor={(item) => String(item.copy_id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load(); }} tintColor={colors.accent} />}
        ListEmptyComponent={<Empty title={folder === "trash" ? "Trash is empty" : "Junk is empty"} />}
        renderItem={({ item }) => (
          <ListRow
            title={item.subject || "(no subject)"}
            subtitle={`${item.from} · ${item.snippet}`}
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
  emptyAction: { padding: 16 },
});
