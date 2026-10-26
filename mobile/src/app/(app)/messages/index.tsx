import { router, useNavigation } from "expo-router";
import { useCallback, useEffect, useLayoutEffect, useState } from "react";
import { FlatList, Platform, Pressable, RefreshControl, StyleSheet, Text, TextInput, useWindowDimensions, View } from "react-native";
import { Path, Svg } from "react-native-svg";
import { ConversationRow } from "@/components/ConversationRow";
import { Empty, Loading, Notice } from "@/components/ui";
import { api, type Chats, type ChatRow } from "@/lib/api";
import { messageFromApiError } from "@/lib/apiError";
import { colors } from "@/theme";

function ComposeIcon() {
  return (
    <Svg width={22} height={22} viewBox="0 0 24 24" fill="none">
      <Path
        d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
        stroke={colors.accent}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <Path
        d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"
        stroke={colors.accent}
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </Svg>
  );
}

type Filter = "all" | "unread" | "direct" | "channels";

const filters: { id: Filter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "unread", label: "Unread" },
  { id: "direct", label: "Direct" },
  { id: "channels", label: "Channels" },
];

type Item =
  | { type: "label"; id: string; title: string }
  | { type: "dm"; id: string; row: ChatRow }
  | { type: "channel"; id: string; row: ChatRow }
  | { type: "project"; id: string; project: Chats["projects"][number] };

function matches(query: string, parts: (string | undefined | null)[]): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return true;
  }
  return parts.some((part) => (part ?? "").toLowerCase().includes(needle));
}

function rows(chats: Chats, query: string, filter: Filter): Item[] {
  const items: Item[] = [];
  const labelSections = filter === "all" || filter === "unread";
  if (filter === "all" || filter === "direct" || filter === "unread") {
    const dms = chats.dms.filter(
      (row) => matches(query, [row.label, row.key, row.preview, ...(row.names ?? [])]) && (filter !== "unread" || row.unread),
    );
    if (dms.length > 0) {
      if (labelSections) {
        items.push({ type: "label", id: "dms", title: "Direct messages" });
      }
      for (const row of dms) {
        items.push({ type: "dm", id: `dm-${row.key}`, row });
      }
    }
  }
  if (filter === "all" || filter === "channels" || filter === "unread") {
    const channels = chats.channels.filter(
      (row) => matches(query, [row.title, row.preview]) && (filter !== "unread" || row.unread),
    );
    if (channels.length > 0) {
      if (labelSections) {
        items.push({ type: "label", id: "channels", title: "Channels" });
      }
      for (const row of channels) {
        items.push({ type: "channel", id: `ch-${row.id}`, row });
      }
    }
  }
  if (filter === "all") {
    const projects = chats.projects.filter((project) => matches(query, [project.name]));
    if (projects.length > 0) {
      items.push({ type: "label", id: "groups", title: "Groups" });
      for (const project of projects) {
        items.push({ type: "project", id: `p-${project.id}`, project });
      }
    }
  }
  return items;
}

function emptyCopy(filter: Filter, query: string): { title: string; hint?: string } {
  if (query.trim()) {
    return { title: "No matches" };
  }
  if (filter === "unread") {
    return { title: "No unread chats" };
  }
  if (filter === "direct") {
    return { title: "No direct messages" };
  }
  if (filter === "channels") {
    return { title: "No channels" };
  }
  return { title: "No conversations yet", hint: "Start a new message." };
}

function ComposeButton({ onPress }: { onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="New message"
      onPress={onPress}
      style={styles.compose}
    >
      <ComposeIcon />
    </Pressable>
  );
}

export default function MessagesScreen() {
  const navigation = useNavigation();
  const { height } = useWindowDimensions();
  const [chats, setChats] = useState<Chats | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      setChats(await api<Chats>("/api/v1/chats/"));
    } catch (err) {
      setError(messageFromApiError(err));
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const openComposer = useCallback(() => router.push("/(app)/messages/new"), []);

  useLayoutEffect(() => {
    if (Platform.OS === "ios") {
      navigation.setOptions({
        title: "Chats",
        headerLargeTitleEnabled: true,
        headerSearchBarOptions: {
          placeholder: "Search",
          autoCapitalize: "none",
          hideWhenScrolling: true,
          placement: "stacked",
          tintColor: colors.accent,
          onChangeText: (event: { nativeEvent: { text: string } }) => setQuery(event.nativeEvent.text),
          onCancelButtonPress: () => setQuery(""),
        },
        unstable_headerRightItems: () => [
          {
            type: "button" as const,
            label: "",
            icon: { type: "sfSymbol" as const, name: "square.and.pencil" as const },
            tintColor: colors.accent,
            accessibilityLabel: "New message",
            onPress: openComposer,
          },
        ],
      });
      return;
    }
    navigation.setOptions({
      title: collapsed ? "Chats" : " ",
      headerLargeTitleEnabled: false,
      headerSearchBarOptions: undefined,
      headerRight: () => <ComposeButton onPress={openComposer} />,
    });
  }, [collapsed, navigation, openComposer]);

  return (
    <View style={styles.flex}>
      <FlatList
        style={styles.list}
        contentInsetAdjustmentBehavior="automatic"
        keyboardShouldPersistTaps="handled"
        scrollEventThrottle={16}
        onScroll={
          Platform.OS === "ios"
            ? undefined
            : (event) => {
                const next = event.nativeEvent.contentOffset.y > 48;
                setCollapsed((current) => (current === next ? current : next));
              }
        }
        contentContainerStyle={Platform.OS === "ios" ? undefined : [styles.webContent, { minHeight: height }]}
        ListHeaderComponent={
          <View>
            {Platform.OS === "ios" ? null : (
              <View style={styles.top}>
                <Text style={styles.largeTitle}>Chats</Text>
                <TextInput
                  value={query}
                  onChangeText={setQuery}
                  placeholder="Search"
                  placeholderTextColor={colors.muted}
                  autoCapitalize="none"
                  autoCorrect={false}
                  accessibilityLabel="Search conversations"
                  style={styles.search}
                />
              </View>
            )}
            <View style={styles.filters}>
              {filters.map((item) => {
                const selected = filter === item.id;
                return (
                  <Pressable
                    key={item.id}
                    accessibilityRole="button"
                    accessibilityState={{ selected }}
                    onPress={() => setFilter(item.id)}
                    style={[styles.pill, selected && styles.pillSelected]}
                  >
                    <Text style={[styles.pillLabel, selected && styles.pillLabelSelected]}>{item.label}</Text>
                  </Pressable>
                );
              })}
            </View>
            {error ? (
              <View style={styles.notice}>
                <Notice text={error} />
              </View>
            ) : null}
          </View>
        }
        data={chats ? rows(chats, query, filter) : []}
        keyExtractor={(item) => item.id}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => {
              setRefreshing(true);
              void load();
            }}
            tintColor={colors.accent}
          />
        }
        ListEmptyComponent={
          !chats && !error ? (
            <Loading />
          ) : error ? undefined : (
            <Empty title={emptyCopy(filter, query).title} hint={emptyCopy(filter, query).hint} />
          )
        }
        renderItem={({ item }) => {
          if (item.type === "label") {
            return <Text style={styles.section}>{item.title}</Text>;
          }
          if (item.type === "dm") {
            const title = item.row.label || item.row.key || "Direct message";
            return (
              <ConversationRow
                title={title}
                subtitle={item.row.preview}
                unread={item.row.unread}
                sortAt={item.row.sort_at}
                names={item.row.names}
                onPress={() =>
                  router.push({ pathname: "/(app)/messages/thread", params: { dm: item.row.key ?? "" } })
                }
              />
            );
          }
          if (item.type === "channel") {
            return (
              <ConversationRow
                title={item.row.title || "Channel"}
                subtitle={item.row.preview}
                sortAt={item.row.sort_at}
                kind="channel"
                onPress={() =>
                  router.push({
                    pathname: "/(app)/messages/thread",
                    params: { channel: String(item.row.id ?? "") },
                  })
                }
              />
            );
          }
          return (
            <ConversationRow
              title={item.project.name}
              subtitle={`${item.project.count} in this group`}
              kind="group"
              onPress={() =>
                router.push({
                  pathname: "/(app)/messages/thread",
                  params: { project: String(item.project.id) },
                })
              }
            />
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.surface },
  list: { flex: 1, backgroundColor: colors.surface },
  webContent: { paddingBottom: 24 },
  top: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 8, gap: 10 },
  largeTitle: { color: colors.text, fontSize: 34, fontWeight: "700", letterSpacing: 0.2 },
  search: {
    backgroundColor: colors.bg,
    borderRadius: 12,
    color: colors.text,
    fontSize: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  filters: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    paddingTop: 4,
    paddingBottom: 10,
  },
  pill: {
    backgroundColor: colors.bg,
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 7,
  },
  pillSelected: { backgroundColor: colors.accent },
  pillLabel: { color: colors.text, fontSize: 14, fontWeight: "600" },
  pillLabelSelected: { color: colors.surface },
  compose: { paddingHorizontal: 12, paddingVertical: 6 },
  notice: { paddingHorizontal: 16, paddingBottom: 8 },
  section: {
    color: colors.muted,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.4,
    textTransform: "uppercase",
    paddingHorizontal: 16,
    paddingTop: 18,
    paddingBottom: 6,
    backgroundColor: colors.surface,
  },
});
