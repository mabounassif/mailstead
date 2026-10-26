import { Tabs, usePathname } from "expo-router";
import { useState, type ReactNode } from "react";
import { Pressable, StyleSheet, Text, View, type ColorValue, type GestureResponderEvent, type StyleProp, type ViewStyle } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { TabIcon, type TabIconName } from "@/components/TabIcon";
import { messageChatCoversTabs } from "@/lib/navigation";
import { ReviewProvider, useReview } from "@/lib/review/store";
import { colors } from "@/theme";

function tabIcon(name: TabIconName) {
  return ({ color, size }: { color: ColorValue; size: number }) => (
    <TabIcon name={name} color={typeof color === "string" ? color : colors.muted} size={size} />
  );
}

function ReviewTabButton({
  style,
  children,
  onPress,
  onLongPress,
  accessibilityLabel,
  accessibilityState,
  testID,
}: {
  style?: StyleProp<ViewStyle>;
  children?: ReactNode;
  onPress?: (event: GestureResponderEvent) => void;
  onLongPress?: (event: GestureResponderEvent) => void;
  accessibilityLabel?: string;
  accessibilityState?: { selected?: boolean; disabled?: boolean };
  testID?: string;
}) {
  const [focused, setFocused] = useState(false);
  return (
    <Pressable
      accessibilityRole="tab"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={accessibilityState}
      testID={testID}
      onPress={onPress}
      onLongPress={onLongPress}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
      style={(state) => [style, styles.reviewHit, state.pressed && styles.reviewPressed, focused && styles.reviewFocused]}
    >
      {children}
    </Pressable>
  );
}

export default function AppLayout() {
  return (
    <ReviewProvider>
      <AppTabs />
    </ReviewProvider>
  );
}

function AppTabs() {
  const insets = useSafeAreaInsets();
  const hideTabs = messageChatCoversTabs(usePathname());
  const review = useReview();
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: hideTabs
          ? { display: "none", height: 0, borderTopWidth: 0 }
          : {
              backgroundColor: colors.surface,
              borderTopColor: colors.border,
              borderTopWidth: StyleSheet.hairlineWidth,
              height: 64 + insets.bottom,
              paddingTop: 4,
              paddingBottom: insets.bottom,
            },
        tabBarLabelStyle: styles.label,
        tabBarItemStyle: styles.item,
        tabBarLabel: ({ color, children }) => (
          <Text numberOfLines={1} style={[styles.label, { color }]}>
            {children}
          </Text>
        ),
      }}
    >
      <Tabs.Screen
        name="messages"
        options={{ title: "Chats", headerShown: false, tabBarIcon: tabIcon("messages") }}
      />
      <Tabs.Screen
        name="drive"
        options={{ title: "Drive", headerShown: false, tabBarIcon: tabIcon("drive") }}
      />
      <Tabs.Screen
        name="review"
        options={{
          title: "Review",
          headerShown: false,
          tabBarShowLabel: false,
          tabBarAccessibilityLabel: review.accessName,
          tabBarBadge: review.badge ?? undefined,
          tabBarBadgeStyle: styles.badge,
          tabBarIcon: ({ color }) => <TabIcon name="review" color={typeof color === "string" ? color : colors.muted} size={22} />,
          tabBarButton: (props) => (
            <ReviewTabButton
              style={props.style}
              accessibilityLabel={props.accessibilityLabel}
              accessibilityState={props.accessibilityState}
              testID={props.testID}
              onPress={props.onPress}
              onLongPress={props.onLongPress}
            >
              {props.children}
            </ReviewTabButton>
          ),
        }}
      />
      <Tabs.Screen
        name="contacts"
        options={{ title: "Contacts", headerShown: false, tabBarIcon: tabIcon("contacts") }}
      />
      <Tabs.Screen
        name="settings"
        options={{ title: "Settings", headerShown: false, tabBarIcon: tabIcon("settings") }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  item: {
    justifyContent: "flex-start",
    paddingTop: 6,
  },
  label: {
    fontSize: 11,
    fontWeight: "600",
    lineHeight: 13,
    marginTop: 2,
    textAlign: "center",
  },
  reviewHit: {
    flex: 1,
    minWidth: 56,
    alignItems: "center",
    justifyContent: "flex-start",
    paddingTop: 6,
  },
  reviewPressed: { opacity: 0.72 },
  reviewFocused: { borderRadius: 16, borderWidth: 2, borderColor: colors.accent },
  badge: {
    backgroundColor: colors.danger,
    color: "#fff",
    fontSize: 11,
    fontWeight: "700",
  },
});
