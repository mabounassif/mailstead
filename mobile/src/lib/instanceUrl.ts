import AsyncStorage from "@react-native-async-storage/async-storage";
import Constants from "expo-constants";
import {
  normalizeInstanceUrl as normalize,
  type NormalizedUrl,
} from "./normalizeInstanceUrl";

export type { NormalizedUrl };
export { sameOrigin } from "./normalizeInstanceUrl";

const STORAGE_KEY = "mailstead.instanceUrl";

export function normalizeInstanceUrl(raw: string): NormalizedUrl | null {
  return normalize(raw, { allowInsecureHttp: __DEV__ });
}

export function getBakedDefaultUrl(): string {
  const extra = Constants.expoConfig?.extra as
    | { defaultInstanceUrl?: string }
    | undefined;
  return (extra?.defaultInstanceUrl ?? "").trim();
}

export async function loadSavedInstanceUrl(): Promise<string | null> {
  const saved = await AsyncStorage.getItem(STORAGE_KEY);
  if (saved) {
    const normalized = normalizeInstanceUrl(saved);
    return normalized?.origin ?? null;
  }
  const baked = getBakedDefaultUrl();
  if (!baked) {
    return null;
  }
  return normalizeInstanceUrl(baked)?.origin ?? null;
}

export async function saveInstanceUrl(origin: string): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, origin);
}

export async function clearInstanceUrl(): Promise<void> {
  await AsyncStorage.removeItem(STORAGE_KEY);
}
