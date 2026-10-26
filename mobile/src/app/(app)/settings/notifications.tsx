import { useCallback, useEffect, useState } from "react";
import { ScrollView, StyleSheet, Switch, Text, View } from "react-native";
import { Button, ListRow, Loading, Notice } from "@/components/ui";
import { api, type DeviceRow, type NotificationPrefs } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { readExpoPushToken } from "@/lib/push";
import { colors } from "@/theme";

const PREVIEW_LABELS: Record<string, string> = {
  private: "Private",
  subject: "Subject only",
  sender_subject: "Sender and subject",
};

export default function NotificationsScreen() {
  const [prefs, setPrefs] = useState<NotificationPrefs | null>(null);
  const [devices, setDevices] = useState<DeviceRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [nextPrefs, nextDevices] = await Promise.all([
        api<NotificationPrefs>("/api/v1/notifications/preferences/"),
        api<{ devices: DeviceRow[] }>("/api/v1/notifications/devices/"),
      ]);
      setPrefs(nextPrefs);
      setDevices(nextDevices.devices);
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function patch(body: Partial<NotificationPrefs>) {
    try {
      setPrefs(await api<NotificationPrefs>("/api/v1/notifications/preferences/", { method: "PATCH", body }));
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }

  async function onRegister() {
    setBusy(true);
    setError(null);
    setInfo(null);
    try {
      const token = await readExpoPushToken();
      await api("/api/v1/notifications/expo/", { method: "POST", body: { token, label: "This phone" } });
      setInfo(prefs?.expo_push_configured ? "This phone is registered." : "This phone is registered. The server still needs an Expo access token before it can deliver push.");
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onTest() {
    setBusy(true);
    setError(null);
    try {
      const result = await api<{ sent: number }>("/api/v1/notifications/test/", { method: "POST" });
      setInfo(result.sent ? "Test notification sent." : "No device accepted the test.");
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onRemove(device: DeviceRow) {
    try {
      await api(`/api/v1/notifications/devices/${device.id}/?kind=${device.kind}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }

  if (!prefs && !error) {
    return <Loading />;
  }

  return (
    <ScrollView contentContainerStyle={styles.body}>
      {error ? <Notice text={error} /> : null}
      {info ? <Notice text={info} tone="info" /> : null}
      {prefs ? (
        <>
          <View style={styles.switchRow}>
            <Text style={styles.label}>Enabled</Text>
            <Switch value={prefs.enabled} onValueChange={(enabled) => void patch({ enabled })} />
          </View>
          <View style={styles.switchRow}>
            <Text style={styles.label}>New mail</Text>
            <Switch value={prefs.new_mail} onValueChange={(new_mail) => void patch({ new_mail })} />
          </View>
          <Text style={styles.label}>Preview</Text>
          {prefs.preview_modes.map((mode) => (
            <ListRow
              key={mode}
              title={PREVIEW_LABELS[mode] ?? mode}
              subtitle={prefs.preview_mode === mode ? "Selected" : undefined}
              onPress={() => void patch({ preview_mode: mode })}
            />
          ))}
          <Text style={styles.note}>
            {prefs.expo_push_configured
              ? "Native push is configured on this server."
              : "Native push is not configured on this server. Web push is unchanged."}
          </Text>
        </>
      ) : null}
      <Button label={busy ? "Working…" : "Register this phone"} onPress={() => void onRegister()} disabled={busy} />
      <Button label="Send a test" tone="quiet" onPress={() => void onTest()} disabled={busy} />
      {devices.map((device) => (
        <ListRow
          key={`${device.kind}-${device.id}`}
          title={device.label}
          subtitle={device.kind === "expo" ? "This app · tap to remove" : "Web browser · tap to remove"}
          onPress={() => void onRemove(device)}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  body: { padding: 16, gap: 12, backgroundColor: colors.bg },
  switchRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  label: { color: colors.text, fontSize: 16 },
  note: { color: colors.muted, fontSize: 14 },
});
