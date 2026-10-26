import { Pressable, StyleSheet, Text, View } from "react-native";
import { Avatar, chatTime } from "@/components/Avatar";
import { colors } from "@/theme";

type Props = {
  title: string;
  subtitle?: string;
  unread?: boolean;
  sortAt?: string | null;
  names?: string[];
  kind?: "person" | "channel" | "group";
  onPress: () => void;
};

export function ConversationRow({ title, subtitle, unread, sortAt, names, kind = "person", onPress }: Props) {
  const time = chatTime(sortAt);
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.row}>
      <Avatar name={title} names={names} kind={kind} />
      <View style={styles.body}>
        <View style={styles.line}>
          <Text style={[styles.title, unread && styles.unread]} numberOfLines={1}>
            {title}
          </Text>
          {time ? <Text style={[styles.time, unread && styles.timeUnread]}>{time}</Text> : null}
        </View>
        <View style={styles.line}>
          <Text style={[styles.preview, unread && styles.previewUnread]} numberOfLines={1}>
            {subtitle || " "}
          </Text>
          {unread ? <View style={styles.dot} /> : null}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    backgroundColor: colors.surface,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  body: { flex: 1, gap: 3 },
  line: { flexDirection: "row", alignItems: "center", gap: 8 },
  title: { flex: 1, color: colors.text, fontSize: 16, fontWeight: "600" },
  unread: { fontWeight: "700" },
  time: { color: colors.muted, fontSize: 12 },
  timeUnread: { color: colors.accent, fontWeight: "700" },
  preview: { flex: 1, color: colors.muted, fontSize: 14 },
  previewUnread: { color: colors.text, fontWeight: "600" },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.accent },
});
