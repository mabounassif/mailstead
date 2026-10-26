import { DefaultTheme, ThemeProvider, usePathname } from "expo-router";
import { NativeTabs } from "expo-router/native-tabs";
import { messageChatCoversTabs } from "@/lib/navigation";
import { ReviewProvider, useReview } from "@/lib/review/store";
import { colors } from "@/theme";

const theme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: colors.accent,
    background: colors.bg,
    card: colors.surface,
    text: colors.text,
    border: colors.border,
    notification: colors.danger,
  },
};

const contentStyle = { backgroundColor: colors.bg };

/** iOS uses the system tab bar: Liquid Glass on iOS 26, frosted material before that. */
export default function IosAppLayout() {
  return (
    <ReviewProvider>
      <IosTabs />
    </ReviewProvider>
  );
}

function IosTabs() {
  const hideTabs = messageChatCoversTabs(usePathname());
  const review = useReview();
  return (
    <ThemeProvider value={theme}>
      <NativeTabs
        hidden={hideTabs}
        disableHiddenAnimation
        tintColor={colors.accent}
        iconColor={{ default: colors.muted, selected: colors.accent }}
        labelStyle={{
          default: { color: colors.muted },
          selected: { color: colors.accent },
        }}
        blurEffect="systemChromeMaterialLight"
        disableTransparentOnScrollEdge
        minimizeBehavior="never"
      >
        <NativeTabs.Trigger name="messages" contentStyle={contentStyle}>
          <NativeTabs.Trigger.Label>Chats</NativeTabs.Trigger.Label>
          <NativeTabs.Trigger.Icon sf={{ default: "message", selected: "message.fill" }} />
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="drive" contentStyle={contentStyle}>
          <NativeTabs.Trigger.Label>Drive</NativeTabs.Trigger.Label>
          <NativeTabs.Trigger.Icon sf={{ default: "internaldrive", selected: "internaldrive.fill" }} />
        </NativeTabs.Trigger>
        <NativeTabs.Trigger
          name="review"
          contentStyle={contentStyle}
          accessibilityLabel={review.accessName}
        >
          <NativeTabs.Trigger.Label hidden>Review</NativeTabs.Trigger.Label>
          <NativeTabs.Trigger.Icon sf={{ default: "bolt.shield", selected: "bolt.shield.fill" }} />
          <NativeTabs.Trigger.Badge hidden={!review.badge}>{review.badge ?? ""}</NativeTabs.Trigger.Badge>
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="contacts" contentStyle={contentStyle}>
          <NativeTabs.Trigger.Label>Contacts</NativeTabs.Trigger.Label>
          <NativeTabs.Trigger.Icon
            sf={{ default: "person.crop.rectangle", selected: "person.crop.rectangle.fill" }}
          />
        </NativeTabs.Trigger>
        <NativeTabs.Trigger name="settings" contentStyle={contentStyle}>
          <NativeTabs.Trigger.Label>Settings</NativeTabs.Trigger.Label>
          <NativeTabs.Trigger.Icon sf={{ default: "gearshape", selected: "gearshape.fill" }} />
        </NativeTabs.Trigger>
      </NativeTabs>
    </ThemeProvider>
  );
}
