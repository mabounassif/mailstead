import { Stack, router } from "expo-router";
import { useEffect } from "react";
import { StatusBar } from "expo-status-bar";
import { setUnauthorizedHandler } from "@/lib/api";
import { colors } from "@/theme";

export default function RootLayout() {
  useEffect(() => {
    setUnauthorizedHandler(() => {
      router.replace("/login");
    });
  }, []);

  return (
    <>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.bg },
          headerTintColor: colors.text,
          headerShadowVisible: false,
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="setup" options={{ title: "Connect instance", headerBackVisible: false }} />
        <Stack.Screen name="login" options={{ title: "Sign in", headerBackVisible: false }} />
        <Stack.Screen name="forgot" options={{ title: "Reset password" }} />
        <Stack.Screen name="reset/[uid]/[token]" options={{ title: "Choose a new password" }} />
        <Stack.Screen name="(app)" options={{ headerShown: false }} />
      </Stack>
    </>
  );
}
