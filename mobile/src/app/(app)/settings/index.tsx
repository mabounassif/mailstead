import { router } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Button, ListRow, Loading, Notice } from "@/components/ui";
import { api, type Me } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { clearInstanceUrl } from "@/lib/instanceUrl";
import { clearStoredReview } from "@/lib/review/storage";
import { clearToken } from "@/lib/session";
import { colors } from "@/theme";

export default function SettingsScreen() {
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setMe(await api<Me>("/api/v1/me/"));
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSignOut() {
    try {
      await api("/api/v1/auth/logout/", { method: "POST" });
    } catch {
      // Local sign-out still leaves the device.
    }
    await clearStoredReview();
    await clearToken();
    router.replace("/login");
  }

  async function onChangeServer() {
    await clearStoredReview();
    await clearToken();
    await clearInstanceUrl();
    router.replace("/setup");
  }

  if (!me && !error) {
    return <Loading />;
  }

  return (
    <View style={styles.body}>
      {me ? (
        <Text style={styles.identity}>
          {me.username}
          {me.mailbox ? `\n${me.mailbox.address}` : "\nNo mailbox on this account"}
        </Text>
      ) : null}
      {error ? <Notice text={error} /> : null}
      <ListRow title="Notifications" onPress={() => router.push("/(app)/settings/notifications")} />
      <ListRow title="Wallets" onPress={() => router.push("/(app)/settings/wallets")} />
      <ListRow title="Passwords" onPress={() => router.push("/(app)/settings/passwords")} />
      <Button label="Sign out" tone="quiet" onPress={() => void onSignOut()} />
      <Button label="Use a different server" tone="quiet" onPress={() => void onChangeServer()} />
    </View>
  );
}

const styles = StyleSheet.create({
  body: { flex: 1, backgroundColor: colors.bg, padding: 16, gap: 12 },
  identity: { color: colors.text, fontSize: 16, marginBottom: 8 },
});
