import { createContext, ReactNode, useContext, useEffect, useMemo, useRef, useState } from "react";
import { DecisionGate, accessName, badgeLabel, isReversible, pendingCount, performDecision, snoozeDeadline, snoozeNotice } from "./queue";
import { clearStoredReview, freshReviewItems, loadStoredReview, writeStoredReview } from "./storage";
import type { DecisionAction, DecisionResult, MailDraft, ReviewItem, SnoozeChoice } from "./types";

type ReviewContextValue = {
  ready: boolean;
  loadError: string | null;
  items: ReviewItem[];
  now: Date;
  count: number;
  badge: string | null;
  accessName: string;
  busyId: string | null;
  notice: string | null;
  canUndo: boolean;
  dismissNotice: () => void;
  retry: () => void;
  decide: (id: string, action: DecisionAction) => Promise<DecisionResult>;
  undo: () => string | null;
  snooze: (id: string, choice: SnoozeChoice) => void;
  updateDraft: (id: string, draft: MailDraft) => void;
  selectOption: (id: string, optionId: string) => void;
  setFeedback: (id: string, feedback: string) => void;
  reset: () => void;
};

const ReviewContext = createContext<ReviewContextValue | null>(null);

export function ReviewProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ReviewItem[] | null>(null);
  const [ready, setReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [now, setNow] = useState(() => new Date());
  const [busyId, setBusyId] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [undoItem, setUndoItem] = useState<ReviewItem | null>(null);
  const itemsRef = useRef<ReviewItem[]>([]);
  const gate = useRef(new DecisionGate());
  itemsRef.current = items ?? [];

  useEffect(() => {
    let active = true;
    setReady(false);
    loadStoredReview()
      .then((loaded) => {
        if (!active) return;
        if (!loaded.ok) {
          setItems([]);
          setLoadError(loaded.message);
          setReady(true);
          return;
        }
        setLoadError(null);
        setItems(loaded.items ?? freshReviewItems(new Date()));
        setReady(true);
      })
      .catch(() => {
        if (!active) return;
        setItems([]);
        setLoadError("The review queue could not be loaded.");
        setReady(true);
      });
    return () => {
      active = false;
    };
  }, [reloadKey]);

  useEffect(() => {
    if (!ready || !items || loadError) return;
    writeStoredReview(items).catch(() => undefined);
  }, [items, loadError, ready]);

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 5000);
    return () => clearInterval(timer);
  }, []);

  const value = useMemo<ReviewContextValue>(() => {
    const list = items ?? [];
    const count = pendingCount(list, now);

    function update(id: string, patch: (item: ReviewItem) => ReviewItem) {
      setItems((current) => (current ? current.map((item) => (item.id === id ? patch(item) : item)) : current));
    }

    return {
      ready,
      loadError,
      items: list,
      now,
      count,
      badge: badgeLabel(count),
      accessName: accessName(count),
      busyId,
      notice,
      canUndo: undoItem !== null,
      dismissNotice: () => {
        setNotice(null);
        setUndoItem(null);
      },
      retry: () => setReloadKey((value) => value + 1),
      decide: async (id, action) => {
        if (!gate.current.tryBegin()) {
          return { ok: false, reason: "busy", message: "A decision is already in progress." };
        }
        setBusyId(id);
        setNotice(null);
        try {
          const item = itemsRef.current.find((entry) => entry.id === id);
          if (!item) {
            return { ok: false, reason: "invalid", message: "This request is no longer in the queue." };
          }
          const result = await performDecision(item, action, { delayMs: 650 });
          if (result.ok) {
            setItems((current) => (current ? current.map((entry) => (entry.id === id ? result.item : entry)) : current));
            setUndoItem(isReversible(action) ? item : null);
            setNotice(result.confirmation);
          } else if (result.reason === "expired") {
            setNow(new Date());
          }
          return result;
        } finally {
          setBusyId(null);
          gate.current.end();
        }
      },
      undo: () => {
        const snapshot = undoItem;
        if (!snapshot || gate.current.tryBegin() === false) return null;
        gate.current.end();
        setItems((current) => (current ? current.map((entry) => (entry.id === snapshot.id ? snapshot : entry)) : current));
        setUndoItem(null);
        setNotice("Restored to pending.");
        return snapshot.id;
      },
      snooze: (id, choice) => {
        if (busyId) return;
        const item = itemsRef.current.find((entry) => entry.id === id);
        if (!item || item.status !== "pending") return;
        const clock = new Date();
        setNow(clock);
        setItems((current) =>
          current
            ? current.map((entry) => (entry.id === id ? { ...entry, snoozeUntil: snoozeDeadline(choice, clock).toISOString() } : entry))
            : current,
        );
        setUndoItem(item);
        setNotice(snoozeNotice(choice, clock));
      },
      updateDraft: (id, draft) => update(id, (item) => ({ ...item, draft })),
      selectOption: (id, optionId) => update(id, (item) => ({ ...item, selectedOptionId: optionId })),
      setFeedback: (id, feedback) => update(id, (item) => ({ ...item, feedback })),
      reset: () => {
        setNotice(null);
        setUndoItem(null);
        setBusyId(null);
        setLoadError(null);
        setNow(new Date());
        setItems(freshReviewItems(new Date()));
      },
    };
  }, [busyId, items, loadError, notice, now, ready, undoItem]);

  return <ReviewContext.Provider value={value}>{children}</ReviewContext.Provider>;
}

export function useReview(): ReviewContextValue {
  const value = useContext(ReviewContext);
  if (!value) {
    throw new Error("Review queue is only available inside the signed-in app.");
  }
  return value;
}

export { clearStoredReview };
