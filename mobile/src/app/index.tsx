import { Redirect } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { loadSavedInstanceUrl } from "@/lib/instanceUrl";
import { colors } from "@/theme";

export default function IndexScreen() {
  const [ready, setReady] = useState(false);
  const [hasInstance, setHasInstance] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const url = await loadSavedInstanceUrl();
      if (!cancelled) {
        setHasInstance(Boolean(url));
        setReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!ready) {
    return (
      <View style={styles.boot}>
        <ActivityIndicator color={colors.accent} size="large" />
      </View>
    );
  }

  if (hasInstance) {
    return <Redirect href="/session" />;
  }
  return <Redirect href="/setup" />;
}

const styles = StyleSheet.create({
  boot: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bg,
  },
});
