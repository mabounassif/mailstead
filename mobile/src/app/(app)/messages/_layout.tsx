import { Stack } from "expo-router";
import { Platform } from "react-native";
import { colors } from "@/theme";

export default function MessagesLayout() {
  return (
    <Stack
      screenOptions={{
        headerTintColor: colors.text,
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.bg },
        ...(Platform.OS === "ios" ? {} : { headerStyle: { backgroundColor: colors.bg } }),
      }}
    >
      <Stack.Screen name="index" options={{ title: "Chats", headerLargeTitleEnabled: true, headerTitleAlign: "left" }} />
      <Stack.Screen name="new" options={{ title: "New message" }} />
      <Stack.Screen name="group" options={{ title: "New group" }} />
      <Stack.Screen name="thread" options={{ title: "Conversation" }} />
      <Stack.Screen name="search" options={{ title: "Search" }} />
      <Stack.Screen name="folder/[name]" options={{ title: "Folder" }} />
      <Stack.Screen name="copy/[copyId]" options={{ title: "Message" }} />
    </Stack>
  );
}
