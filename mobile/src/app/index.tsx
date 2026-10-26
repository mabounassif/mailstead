import { Redirect } from "expo-router";
import { useEffect, useState } from "react";
import { loadSavedInstanceUrl } from "@/lib/instanceUrl";
import { loadToken } from "@/lib/session";
import { Loading } from "@/components/ui";

export default function IndexScreen() {
  const [dest, setDest] = useState<"setup" | "login" | "app" | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const url = await loadSavedInstanceUrl();
      if (cancelled) {
        return;
      }
      if (!url) {
        setDest("setup");
        return;
      }
      const token = await loadToken();
      if (!cancelled) {
        setDest(token ? "app" : "login");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (dest === "setup") {
    return <Redirect href="/setup" />;
  }
  if (dest === "login") {
    return <Redirect href="/login" />;
  }
  if (dest === "app") {
    return <Redirect href="/(app)/messages" />;
  }
  return <Loading />;
}
