import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { Empty, ListRow, Loading, Notice } from "@/components/ui";
import { api, type DriveFile } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { downloadAuthed } from "@/lib/download";
import { colors } from "@/theme";

type DriveResponse = {
  files: DriveFile[];
  disk_used: string;
  disk_total: string;
  disk_free: string;
};

export default function DriveScreen() {
  const [drive, setDrive] = useState<DriveResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      setDrive(await api<DriveResponse>("/api/v1/drive/"));
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (!drive && !error) {
    return <Loading />;
  }

  return (
    <View style={styles.flex}>
      {drive ? (
        <Text style={styles.capacity}>
          {drive.disk_used} used · {drive.disk_free} free of {drive.disk_total}
        </Text>
      ) : null}
      {error ? <Notice text={error} /> : null}
      <FlatList
        data={drive?.files ?? []}
        keyExtractor={(item) => `${item.copy_id}-${item.attachment_id}`}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load(); }} tintColor={colors.accent} />}
        ListEmptyComponent={<Empty title="No files yet" hint="Attachments from your mail show up here." />}
        renderItem={({ item }) => (
          <ListRow
            title={item.name}
            subtitle={`${item.size} · ${item.subject}${item.local ? "" : " · not on this server"}`}
            onPress={
              item.local
                ? () =>
                    void downloadAuthed(
                      `/api/v1/messages/${item.copy_id}/attachments/${item.attachment_id}/`,
                      item.name,
                    ).catch((err) => setError(messageFromApiError(err)))
                : undefined
            }
          />
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  capacity: { color: colors.muted, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8 },
});
