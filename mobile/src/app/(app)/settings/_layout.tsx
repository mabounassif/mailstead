import { Stack } from "expo-router";
import { colors } from "@/theme";

export default function SettingsLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg },
        headerTintColor: colors.text,
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.bg },
      }}
    >
      <Stack.Screen name="index" options={{ title: "Settings" }} />
      <Stack.Screen name="notifications" options={{ title: "Notifications" }} />
      <Stack.Screen name="wallets" options={{ title: "Wallets" }} />
      <Stack.Screen name="passwords" options={{ title: "Passwords" }} />
    </Stack>
  );
}
