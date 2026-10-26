import { router, useLocalSearchParams, useNavigation } from "expo-router";
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  FlatList,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Avatar, avatarColor, chatTime } from "@/components/Avatar";
import { Empty, Loading, Notice } from "@/components/ui";
import { api, type ChatMessage, type Conversation, type SendResult } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

function query(params: { dm?: string; channel?: string; project?: string; contact?: string }) {
  const search = new URLSearchParams();
  if (params.channel) search.set("channel", params.channel);
  else if (params.dm) search.set("dm", params.dm);
  else if (params.project) search.set("project", params.project);
  else if (params.contact) search.set("contact", params.contact);
  return search.toString();
}

function one(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function sameSender(current: ChatMessage, previous: ChatMessage | undefined): boolean {
  if (!previous || current.kind !== "message" || previous.kind !== "message") {
    return false;
  }
  return Boolean(current.outgoing) === Boolean(previous.outgoing) && (current.who || "") === (previous.who || "");
}

export default function ThreadScreen() {
  const params = useLocalSearchParams<{ dm?: string; channel?: string; project?: string; contact?: string }>();
  const dm = one(params.dm);
  const channel = one(params.channel);
  const project = one(params.project);
  const contact = one(params.contact);
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();
  const [keyboardOpen, setKeyboardOpen] = useState(false);
  const listRef = useRef<FlatList<ChatMessage>>(null);
  const [chat, setChat] = useState<Conversation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [body, setBody] = useState("");
  const [add, setAdd] = useState("");
  const [drop, setDrop] = useState("");
  const [busy, setBusy] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    const qs = query({ dm, channel, project, contact });
    if (!qs) {
      setError("Choose a conversation.");
      return;
    }
    try {
      setError(null);
      setChat(await api<Conversation>(`/api/v1/conversations/?${qs}`));
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setRefreshing(false);
    }
  }, [dm, channel, project, contact]);

  useLayoutEffect(() => {
    const label = chat?.label || "Conversation";
    navigation.setOptions({
      headerTitle: () => (
        <View style={styles.headerTitle}>
          <Avatar
            name={label}
            kind={channel ? "channel" : project ? "group" : "person"}
            size={32}
          />
          <Text style={styles.headerLabel} numberOfLines={1}>
            {label}
          </Text>
        </View>
      ),
    });
  }, [channel, chat?.label, navigation, project]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const showEvent = Platform.OS === "ios" ? "keyboardWillShow" : "keyboardDidShow";
    const hideEvent = Platform.OS === "ios" ? "keyboardWillHide" : "keyboardDidHide";
    const show = Keyboard.addListener(showEvent, () => setKeyboardOpen(true));
    const hide = Keyboard.addListener(hideEvent, () => setKeyboardOpen(false));
    return () => {
      show.remove();
      hide.remove();
    };
  }, []);

  async function onSend() {
    if (!chat) return;
    setBusy(true);
    setError(null);
    try {
      const payload = { body, subject: chat.subject, add: add.trim(), drop };
      if (chat.conversation_id && chat.mode !== "group") {
        await api<SendResult>(`/api/v1/conversations/${chat.conversation_id}/messages/`, {
          method: "POST",
          body: payload,
        });
      } else {
        await api<SendResult>("/api/v1/conversations/", {
          method: "POST",
          body: {
            ...payload,
            dm: dm || chat.dm_key || "",
            channel_id: channel ? Number(channel) : undefined,
            project_id: project ? Number(project) : chat.project_id,
            contact: contact || chat.contact || "",
          },
        });
      }
      setBody("");
      setAdd("");
      setDrop("");
      await load();
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setBusy(false);
    }
  }

  if (!chat && !error) {
    return <Loading />;
  }

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      {error ? <Notice text={error} /> : null}
      <FlatList
        ref={listRef}
        data={chat?.messages ?? []}
        keyExtractor={(item, index) => `${item.kind}-${item.copy_id ?? index}`}
        contentContainerStyle={styles.transcript}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: false })}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); void load(); }} tintColor={colors.accent} />
        }
        ListEmptyComponent={<Empty title="No messages yet" />}
        renderItem={({ item, index }) => {
          if (item.kind === "event") {
            return <Text style={styles.event}>{item.body}</Text>;
          }
          const previous = chat?.messages[index - 1];
          const clustered = sameSender(item, previous);
          const who = item.who || "";
          const time = chatTime(item.sort_at);
          return (
            <View style={[styles.message, item.outgoing ? styles.messageOut : styles.messageIn, clustered && styles.clustered]}>
              {item.outgoing ? null : clustered ? (
                <View style={styles.avatarGap} />
              ) : (
                <Avatar name={who || chat?.label || "?"} size={32} />
              )}
              <Pressable
                accessibilityRole="button"
                onPress={() =>
                  item.copy_id
                    ? router.push({ pathname: "/(app)/messages/copy/[copyId]", params: { copyId: String(item.copy_id) } })
                    : undefined
                }
                style={[styles.bubble, item.outgoing ? styles.out : styles.in, clustered && (item.outgoing ? styles.outCluster : styles.inCluster)]}
              >
                {!item.outgoing && !clustered && who ? (
                  <Text style={[styles.who, { color: avatarColor(who) }]}>{who}</Text>
                ) : null}
                <Text style={[styles.preview, item.outgoing && styles.previewOut]}>{item.preview || item.title}</Text>
                {time ? <Text style={[styles.time, item.outgoing && styles.timeOut]}>{time}</Text> : null}
              </Pressable>
            </View>
          );
        }}
      />
      {chat?.participants?.length ? (
        <View style={styles.people}>
          {chat.participants.map((person) => {
            const name = person.display_name || person.address;
            const removing = drop === person.address;
            return (
              <Pressable
                key={person.address}
                accessibilityRole="button"
                disabled={person.kind !== "cc"}
                onPress={() => person.kind === "cc" && setDrop(removing ? "" : person.address)}
                style={[styles.person, removing && styles.personRemoving]}
              >
                <Avatar name={name} size={22} />
                <Text style={styles.personName} numberOfLines={1}>
                  {removing ? `Remove ${name}` : name}
                </Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}
      {chat?.can_compose ? (
        <View style={[styles.composer, { paddingBottom: keyboardOpen ? 10 : Math.max(insets.bottom, 10) }]}>
          <TextInput
            value={add}
            onChangeText={setAdd}
            placeholder="Add an email"
            placeholderTextColor={colors.muted}
            autoCapitalize="none"
            autoCorrect={false}
            style={styles.add}
          />
          <View style={styles.sendRow}>
            <TextInput
              value={body}
              onChangeText={setBody}
              placeholder="Message"
              placeholderTextColor={colors.muted}
              style={styles.input}
              multiline
            />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Send"
              disabled={busy || (!body.trim() && !add.trim())}
              onPress={() => void onSend()}
              style={[styles.send, (busy || (!body.trim() && !add.trim())) && styles.sendDisabled]}
            >
              <Text style={styles.sendText}>{busy ? "…" : "↑"}</Text>
            </Pressable>
          </View>
        </View>
      ) : null}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  headerTitle: { flexDirection: "row", alignItems: "center", gap: 8, maxWidth: 240 },
  headerLabel: { color: colors.text, fontSize: 17, fontWeight: "600", flexShrink: 1 },
  transcript: { paddingVertical: 12, flexGrow: 1 },
  message: { flexDirection: "row", alignItems: "flex-start", gap: 8, paddingHorizontal: 12, marginTop: 10 },
  messageIn: { justifyContent: "flex-start" },
  messageOut: { justifyContent: "flex-end" },
  clustered: { marginTop: 2 },
  avatarGap: { width: 32 },
  bubble: { maxWidth: "78%", borderRadius: 18, paddingHorizontal: 12, paddingTop: 8, paddingBottom: 6 },
  in: { backgroundColor: colors.surface, borderBottomLeftRadius: 6 },
  out: { backgroundColor: colors.accent, borderBottomRightRadius: 6 },
  inCluster: { borderTopLeftRadius: 8 },
  outCluster: { borderTopRightRadius: 8 },
  who: { fontSize: 13, fontWeight: "700", marginBottom: 2 },
  preview: { color: colors.text, fontSize: 16, lineHeight: 21 },
  previewOut: { color: "#fff" },
  time: { color: colors.muted, fontSize: 11, alignSelf: "flex-end", marginTop: 4 },
  timeOut: { color: "rgba(255,255,255,0.8)" },
  event: { color: colors.muted, textAlign: "center", marginVertical: 10, paddingHorizontal: 24, fontSize: 13 },
  people: { flexDirection: "row", flexWrap: "wrap", gap: 8, paddingHorizontal: 12, paddingBottom: 8 },
  person: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingRight: 10,
    paddingVertical: 3,
    paddingLeft: 3,
    maxWidth: "70%",
  },
  personRemoving: { backgroundColor: "#fce8e6" },
  personName: { color: colors.text, fontSize: 13, flexShrink: 1 },
  composer: {
    borderTopColor: colors.border,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: 10,
    gap: 8,
    backgroundColor: colors.surface,
  },
  add: { color: colors.text, fontSize: 14, paddingHorizontal: 4 },
  sendRow: { flexDirection: "row", alignItems: "flex-end", gap: 8 },
  input: {
    flex: 1,
    color: colors.text,
    fontSize: 16,
    maxHeight: 120,
    backgroundColor: colors.bg,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  send: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
  },
  sendDisabled: { opacity: 0.45 },
  sendText: { color: "#fff", fontSize: 18, fontWeight: "700", marginTop: -1 },
});
