import { StyleSheet, Text, View } from "react-native";

const PALETTE = ["#1a73e8", "#0b8043", "#e37400", "#9334e6", "#d93025", "#129eaf", "#7b1fa2", "#c26401"];

export function avatarColor(seed: string): string {
  let hash = 0;
  for (const char of seed) {
    hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  }
  return PALETTE[hash % PALETTE.length];
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return "?";
  }
  const first = parts[0].replace(/[^a-z0-9]/gi, "");
  if (parts.length === 1) {
    return (first.slice(0, 1) || "?").toUpperCase();
  }
  const last = parts[parts.length - 1].replace(/[^a-z0-9]/gi, "");
  return `${(first.slice(0, 1) || "?").toUpperCase()}${(last.slice(0, 1) || "").toUpperCase()}`;
}

export function chatTime(iso?: string | null): string {
  if (!iso) {
    return "";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  }
  const age = now.getTime() - date.getTime();
  if (age >= 0 && age < 6 * 24 * 60 * 60 * 1000) {
    return date.toLocaleDateString(undefined, { weekday: "short" });
  }
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

type Props = {
  name: string;
  names?: string[];
  kind?: "person" | "channel" | "group";
  size?: number;
};

export function Avatar({ name, names, kind = "person", size = 48 }: Props) {
  const people = (names ?? []).map((person) => person.trim()).filter(Boolean).slice(0, 2);
  const many = kind === "person" && people.length > 1;
  const label = name.trim() || people[0] || "?";
  const background = kind === "channel" ? "#e8f0fe" : avatarColor(label);
  const mark = kind === "channel" ? "#" : initials(label);

  if (many) {
    const face = size * 0.62;
    return (
      <View accessibilityElementsHidden style={[styles.circle, { width: size, height: size }]}>
        {people.map((person, index) => (
          <View
            key={`${person}-${index}`}
            style={{
              width: face,
              height: face,
              borderRadius: face / 2,
              backgroundColor: avatarColor(person),
              borderWidth: 2,
              borderColor: "#fff",
              alignItems: "center",
              justifyContent: "center",
              marginLeft: index === 0 ? 0 : -size * 0.24,
              zIndex: people.length - index,
            }}
          >
            <Text style={[styles.letter, { fontSize: face * 0.42, color: "#fff" }]}>{initials(person).slice(0, 1)}</Text>
          </View>
        ))}
      </View>
    );
  }

  return (
    <View
      accessibilityElementsHidden
      style={[
        styles.circle,
        {
          width: size,
          height: size,
          borderRadius: size / 2,
          backgroundColor: background,
        },
      ]}
    >
      <Text style={[styles.letter, { fontSize: size * (mark.length > 1 ? 0.34 : 0.4), color: kind === "channel" ? "#1a73e8" : "#fff" }]}>
        {mark}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  circle: {
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },
  letter: { fontWeight: "700" },
});
