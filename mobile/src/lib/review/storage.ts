import AsyncStorage from "@react-native-async-storage/async-storage";
import { createFixtures, isItem, normalizeItem } from "./queue";
import type { ReviewItem } from "./types";

export const REVIEW_STORAGE_KEY = "mailstead.reviewQueue.v1";

type Stored = { version: 1; items: ReviewItem[] };

export type ReviewLoad =
  | { ok: true; items: ReviewItem[] | null }
  | { ok: false; message: string };

export async function loadStoredReview(): Promise<ReviewLoad> {
  try {
    const raw = await AsyncStorage.getItem(REVIEW_STORAGE_KEY);
    if (!raw) return { ok: true, items: null };
    const parsed = JSON.parse(raw) as Stored;
    if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.items) || !parsed.items.every(isItem)) {
      return { ok: true, items: null };
    }
    return { ok: true, items: parsed.items.map(normalizeItem) };
  } catch {
    return { ok: false, message: "The review queue could not be loaded." };
  }
}

export async function readStoredReview(): Promise<ReviewItem[] | null> {
  const loaded = await loadStoredReview();
  if (!loaded.ok) return null;
  return loaded.items;
}

export async function writeStoredReview(items: ReviewItem[]): Promise<void> {
  await AsyncStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify({ version: 1, items }));
}

export async function clearStoredReview(): Promise<void> {
  await AsyncStorage.removeItem(REVIEW_STORAGE_KEY);
}

export function freshReviewItems(now = new Date()): ReviewItem[] {
  return createFixtures(now);
}
