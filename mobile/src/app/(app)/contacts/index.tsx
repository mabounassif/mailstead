import { router } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, View } from "react-native";
import { ConversationRow } from "@/components/ConversationRow";
import { Empty, Loading, Notice } from "@/components/ui";
import { api, type ContactRow } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

export default function ContactsScreen() {
  const [contacts, setContacts] = useState<ContactRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const body = await api<{ contacts: ContactRow[] }>("/api/v1/contacts/");
      setContacts(body.contacts);
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (!contacts && !error) {
    return <Loading />;
  }

  return (
    <View style={{ flex: 1, backgroundColor: colors.surface }}>
      {error ? <Notice text={error} /> : null}
      <FlatList
        style={{ backgroundColor: colors.surface }}
        data={contacts ?? []}
        keyExtractor={(item) => item.address}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load(); }} tintColor={colors.accent} />}
        ListEmptyComponent={<Empty title="No contacts yet" hint="People appear from your conversations." />}
        renderItem={({ item }) => (
          <ConversationRow
            title={item.label || item.address}
            subtitle={item.preview || item.address}
            unread={item.unread}
            sortAt={item.sort_at}
            onPress={() =>
              router.push({ pathname: "/(app)/messages/thread", params: { contact: item.address } })
            }
          />
        )}
      />
    </View>
  );
}
