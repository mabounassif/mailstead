import { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
} from "react-native";
import { colors } from "@/theme";

export function Loading() {
  return (
    <View style={styles.center}>
      <ActivityIndicator color={colors.accent} size="large" />
    </View>
  );
}

export function Notice({ text, tone = "error" }: { text: string; tone?: "error" | "info" }) {
  return <Text style={tone === "info" ? styles.info : styles.notice}>{text}</Text>;
}

export function Empty({ title, hint }: { title: string; hint?: string }) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyTitle}>{title}</Text>
      {hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

export function TextField(props: TextInputProps & { label: string }) {
  const { label, style, ...rest } = props;
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.muted}
        style={[styles.input, style]}
        {...rest}
      />
    </View>
  );
}

export function Button({
  label,
  onPress,
  disabled,
  tone = "primary",
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  tone?: "primary" | "quiet" | "danger";
}) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={[styles.button, tone === "quiet" && styles.quiet, tone === "danger" && styles.danger, disabled && styles.disabled]}
    >
      <Text style={[styles.buttonText, tone === "quiet" && styles.quietText]}>{label}</Text>
    </Pressable>
  );
}

export function ListRow({
  title,
  subtitle,
  onPress,
  unread,
}: {
  title: string;
  subtitle?: string;
  onPress?: () => void;
  unread?: boolean;
}) {
  return (
    <Pressable accessibilityRole="button" disabled={!onPress} onPress={onPress} style={styles.row}>
      <Text style={[styles.rowTitle, unread && styles.unread]} numberOfLines={1}>
        {title}
      </Text>
      {subtitle ? (
        <Text style={styles.rowSubtitle} numberOfLines={2}>
          {subtitle}
        </Text>
      ) : null}
    </Pressable>
  );
}

export function ScreenBody({ children }: { children: ReactNode }) {
  return <View style={styles.body}>{children}</View>;
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: colors.bg },
  body: { flex: 1, backgroundColor: colors.bg, padding: 16, gap: 12 },
  notice: { color: colors.danger, fontSize: 15 },
  info: { color: colors.text, fontSize: 15 },
  empty: { paddingVertical: 32, gap: 6 },
  emptyTitle: { color: colors.text, fontSize: 18, fontWeight: "600" },
  hint: { color: colors.muted, fontSize: 15 },
  field: { gap: 6 },
  label: { color: colors.muted, fontSize: 13 },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 10,
    color: colors.text,
    fontSize: 16,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  button: {
    backgroundColor: colors.accent,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
  },
  quiet: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  danger: { backgroundColor: colors.danger },
  disabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  quietText: { color: colors.text },
  row: {
    backgroundColor: colors.surface,
    borderBottomColor: colors.border,
    borderBottomWidth: StyleSheet.hairlineWidth,
    paddingHorizontal: 16,
    paddingVertical: 14,
    gap: 4,
  },
  rowTitle: { color: colors.text, fontSize: 16 },
  unread: { fontWeight: "700" },
  rowSubtitle: { color: colors.muted, fontSize: 14 },
});
