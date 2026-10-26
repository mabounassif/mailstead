import { router, useLocalSearchParams } from "expo-router";
import { useCallback, useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { HtmlMail } from "@/components/HtmlMail";
import { Button, Loading, Notice } from "@/components/ui";
import { api, type MessageDetail } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { downloadAuthed } from "@/lib/download";
import { colors } from "@/theme";

export default function MessageScreen() {
  const { copyId } = useLocalSearchParams<{ copyId: string }>();
  const [detail, setDetail] = useState<MessageDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [images, setImages] = useState(false);
  const [reply, setReply] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async (loadImages: boolean) => {
    try {
      setError(null);
      const path = `/api/v1/messages/${copyId}/${loadImages ? "?load_images=1" : ""}`;
      setDetail(await api<MessageDetail>(path));
      setImages(loadImages);
    } catch (err) {
      setError(messageFromApiError(err));
    }
  }, [copyId]);

  useEffect(() => {
    void load(false);
  }, [load]);

  const anchor = detail?.thread.find((item) => item.kind === "message" && item.is_anchor) ?? detail?.thread.find((item) => item.kind === "message");

  async function act(path: string, body?: unknown) {
    setBusy(true);
    setError(null);
    try {
      await api(path, { method: "POST", body: body ?? {} });
      if (path.endsWith("/trash/") || path.endsWith("/purge/") || path.endsWith("/restore/")) {
        router.back();
        return;
      }
      if (path.endsWith("/reply/") || path.endsWith("/reply-all/")) {
        setReply("");
      }
      await load(images);
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  if (!detail && !error) {
    return <Loading />;
  }

  return (
    <View style={styles.flex}>
      <ScrollView contentContainerStyle={styles.header}>
        <Text style={styles.subject}>{anchor?.subject || "(no subject)"}</Text>
        <Text style={styles.from}>{anchor?.from}</Text>
        {anchor?.text ? <Text style={styles.text}>{anchor.text}</Text> : null}
        {anchor?.bcc ? <Text style={styles.bcc}>Bcc: {anchor.bcc}</Text> : null}
        {error ? <Notice text={error} /> : null}
        {anchor?.attachments?.map((attachment) => (
          <Pressable
            key={attachment.id}
            accessibilityRole="button"
            disabled={!attachment.downloadable}
            onPress={() =>
              void downloadAuthed(
                `/api/v1/messages/${copyId}/attachments/${attachment.id}/`,
                attachment.filename || "attachment",
              ).catch((err) => setError(messageFromApiError(err)))
            }
          >
            <Text style={styles.link}>{attachment.filename || "Attachment"}</Text>
          </Pressable>
        ))}
        <View style={styles.actions}>
          {detail?.folder !== "trash" ? (
            <Button label="Trash" tone="quiet" onPress={() => void act(`/api/v1/messages/${copyId}/trash/`)} disabled={busy} />
          ) : (
            <>
              <Button label="Restore" tone="quiet" onPress={() => void act(`/api/v1/messages/${copyId}/restore/`)} disabled={busy} />
              <Button label="Delete" tone="danger" onPress={() => void act(`/api/v1/messages/${copyId}/purge/`)} disabled={busy} />
            </>
          )}
          {detail?.folder === "junk" ? (
            <Button label="Not junk" tone="quiet" onPress={() => void act(`/api/v1/messages/${copyId}/not-junk/`)} disabled={busy} />
          ) : detail?.folder !== "trash" ? (
            <Button label="Junk" tone="quiet" onPress={() => void act(`/api/v1/messages/${copyId}/junk/`)} disabled={busy} />
          ) : null}
          <Button
            label="Export"
            tone="quiet"
            onPress={() => void downloadAuthed(`/api/v1/messages/${copyId}/eml/`, "message.eml").catch((err) => setError(messageFromApiError(err)))}
            disabled={busy}
          />
        </View>
      </ScrollView>
      {anchor?.html ? (
        <HtmlMail html={anchor.html} onLoadImages={images ? undefined : () => void load(true)} />
      ) : null}
      {detail?.can_reply ? (
        <View style={styles.reply}>
          <TextInput
            value={reply}
            onChangeText={setReply}
            placeholder={`Reply to ${detail.reply_to}`}
            placeholderTextColor={colors.muted}
            style={styles.input}
            multiline
          />
          <View style={styles.replyActions}>
            <Button label="Reply" onPress={() => void act(`/api/v1/messages/${copyId}/reply/`, { body: reply })} disabled={busy} />
            <Button label="Reply all" tone="quiet" onPress={() => void act(`/api/v1/messages/${copyId}/reply-all/`, { body: reply })} disabled={busy} />
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  header: { padding: 16, gap: 8 },
  subject: { color: colors.text, fontSize: 20, fontWeight: "600" },
  from: { color: colors.muted, fontSize: 14 },
  text: { color: colors.text, fontSize: 16 },
  bcc: { color: colors.muted, fontSize: 13 },
  link: { color: colors.accent, fontSize: 15 },
  actions: { gap: 8 },
  reply: { borderTopColor: colors.border, borderTopWidth: StyleSheet.hairlineWidth, padding: 12, gap: 8, backgroundColor: colors.surface },
  input: { color: colors.text, fontSize: 16, minHeight: 44 },
  replyActions: { flexDirection: "row", gap: 8 },
});
