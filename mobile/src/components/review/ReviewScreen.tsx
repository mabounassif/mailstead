import { router } from "expo-router";
import { useEffect, useRef, useState, type ComponentRef, type Ref } from "react";
import {
  AccessibilityInfo,
  ActivityIndicator,
  findNodeHandle,
  KeyboardAvoidingView,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  useWindowDimensions,
  View,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { Line, Rect, Svg } from "react-native-svg";
import { Avatar } from "@/components/Avatar";
import { Empty } from "@/components/ui";
import { useReduceMotion } from "@/components/review/useReduceMotion";
import {
  actionLabel,
  authorizationCopy,
  browseTo,
  browsingEnabled,
  busyLabel,
  confirmationCopy,
  deckLayout,
  destinationAfterLater,
  expirationCopy,
  formatDateTime,
  formatRequested,
  indexAfterResolve,
  isExpired,
  isSnoozed,
  offersChanges,
  primaryAction,
  requiresConfirmation,
  reviewedItems,
  statusLabel,
  visiblePending,
} from "@/lib/review/queue";
import { useReview } from "@/lib/review/store";
import type { DecisionAction, ReviewItem, SnoozeChoice } from "@/lib/review/types";
import { colors } from "@/theme";

type Mode = "cards" | "list" | "reviewed";

function focusNode(node: ComponentRef<typeof View> | null) {
  if (!node) return;
  const focusable = node as { focus?: () => void };
  if (typeof focusable.focus === "function") {
    focusable.focus();
    return;
  }
  const handle = findNodeHandle(node as never);
  if (handle) AccessibilityInfo.setAccessibilityFocus(handle);
}

function kindLabel(kind: ReviewItem["requester"]["kind"]): string {
  if (kind === "agent") return "Agent";
  if (kind === "app") return "App";
  return "Person";
}

function LayoutIcon({ kind, color }: { kind: "list" | "card"; color: string }) {
  const ink = { stroke: color, strokeWidth: 2, strokeLinecap: "round" as const };
  return (
    <Svg width={18} height={18} viewBox="0 0 24 24" fill="none">
      {kind === "list" ? (
        <>
          <Line x1="8" x2="21" y1="6" y2="6" {...ink} />
          <Line x1="8" x2="21" y1="12" y2="12" {...ink} />
          <Line x1="8" x2="21" y1="18" y2="18" {...ink} />
          <Line x1="3" x2="3.01" y1="6" y2="6" {...ink} />
          <Line x1="3" x2="3.01" y1="12" y2="12" {...ink} />
          <Line x1="3" x2="3.01" y1="18" y2="18" {...ink} />
        </>
      ) : (
        <>
          <Rect x="4" y="4" width="16" height="16" rx="2" stroke={color} strokeWidth={2} />
          <Line x1="4" x2="20" y1="9" y2="9" {...ink} />
        </>
      )}
    </Svg>
  );
}

export function ReviewScreen() {
  const review = useReview();
  const insets = useSafeAreaInsets();
  const { ready, items, now, busyId, notice, loadError, canUndo } = review;
  const reduceMotion = useReduceMotion();
  const { width } = useWindowDimensions();
  const layout = deckLayout(width);
  const wide = width >= 840;
  const pending = visiblePending(items, now);
  const reviewed = reviewedItems(items);
  const snoozedCount = items.filter((item) => isSnoozed(item, now)).length;
  const [mode, setMode] = useState<Mode>("cards");
  const [index, setIndex] = useState(0);
  const [stageHeight, setStageHeight] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [changesOpen, setChangesOpen] = useState(false);
  const [snoozeOpen, setSnoozeOpen] = useState(false);
  const [confirm, setConfirm] = useState<DecisionAction | null>(null);
  const [activeAction, setActiveAction] = useState<DecisionAction | null>(null);
  const [focusToken, setFocusToken] = useState(0);
  const [restoreId, setRestoreId] = useState<string | null>(null);
  const scroller = useRef<ComponentRef<typeof ScrollView>>(null);
  const headingRef = useRef<ComponentRef<typeof View>>(null);
  const programmatic = useRef(false);
  const announced = useRef(false);
  const place = useRef({ index, mode });

  const current = pending[index] ?? pending[pending.length - 1];

  useEffect(() => {
    if (index > pending.length - 1) setIndex(Math.max(0, pending.length - 1));
  }, [index, pending.length]);

  useEffect(() => {
    if (place.current.index === index && place.current.mode === mode) return;
    place.current = { index, mode };
    setChangesOpen(false);
    setSnoozeOpen(false);
    setConfirm(null);
  }, [index, mode]);

  useEffect(() => {
    if (!restoreId) return;
    const next = visiblePending(items, now).findIndex((item) => item.id === restoreId);
    if (next >= 0) setIndex(next);
    setRestoreId(null);
  }, [items, now, restoreId]);

  useEffect(() => {
    const node = scroller.current;
    if (!node || mode !== "cards" || pending.length === 0) return;
    programmatic.current = true;
    node.scrollTo({
      x: Math.max(0, index) * (layout.cardWidth + layout.gap),
      animated: !reduceMotion,
    });
    const timer = setTimeout(() => {
      programmatic.current = false;
    }, reduceMotion ? 0 : 320);
    return () => clearTimeout(timer);
  }, [index, layout.cardWidth, layout.gap, mode, pending.length, reduceMotion]);

  useEffect(() => {
    if (!focusToken) return;
    focusNode(headingRef.current);
  }, [focusToken, mode, index, pending.length]);

  useEffect(() => {
    if (!announced.current) {
      announced.current = true;
      return;
    }
    if (mode !== "cards" || pending.length === 0 || Platform.OS === "web") return;
    AccessibilityInfo.announceForAccessibility(`${index + 1} of ${pending.length}`);
  }, [index, mode, pending.length]);

  useEffect(() => {
    if (!notice || Platform.OS === "web") return;
    AccessibilityInfo.announceForAccessibility(notice);
  }, [notice]);

  useEffect(() => {
    if (Platform.OS !== "web") return;
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || target?.isContentEditable) return;
      if (mode !== "cards" || confirm || pending.length < 2) return;
      if (event.key === "ArrowRight") {
        event.preventDefault();
        setIndex((value) => browseTo(value, 1, pending.length));
      }
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        setIndex((value) => browseTo(value, -1, pending.length));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [confirm, mode, pending.length]);

  function settle(offsetX: number) {
    if (programmatic.current || pending.length === 0) return;
    const step = layout.cardWidth + layout.gap;
    const next = Math.round(offsetX / Math.max(step, 1));
    const clamped = Math.max(0, Math.min(pending.length - 1, next));
    setIndex((value) => (value === clamped ? value : clamped));
  }

  function toggle(key: string) {
    setOpen((currentOpen) => ({ ...currentOpen, [key]: !currentOpen[key] }));
  }

  async function onDecide(action: DecisionAction) {
    if (!current || busyId) return;
    const before = pending.map((item) => item.id);
    setConfirm(null);
    setActiveAction(action);
    setError(null);
    let result;
    try {
      result = await review.decide(current.id, action);
    } finally {
      setActiveAction(null);
    }
    if (!result.ok) {
      setError(result.message);
      return;
    }
    const nextIndex = indexAfterResolve(before, current.id);
    setChangesOpen(false);
    setSnoozeOpen(false);
    setIndex(nextIndex < 0 ? 0 : nextIndex);
    setFocusToken((token) => token + 1);
  }

  function onPrimary(item: ReviewItem) {
    const action = primaryAction(item, now);
    if (item.kind === "appointment" && !item.selectedOptionId) return;
    if (requiresConfirmation(action)) {
      setConfirm(action);
      return;
    }
    void onDecide(action);
  }

  function onSnooze(choice: SnoozeChoice | "next") {
    if (!current || busyId) return;
    setSnoozeOpen(false);
    if (choice === "next") {
      const dest = destinationAfterLater(
        pending.map((item) => item.id),
        current.id,
      );
      if (dest.type === "list") {
        setMode("list");
        setFocusToken((token) => token + 1);
        return;
      }
      const next = pending.findIndex((item) => item.id === dest.id);
      if (next >= 0) setIndex(next);
      return;
    }
    const before = pending.map((item) => item.id);
    review.snooze(current.id, choice);
    const nextIndex = indexAfterResolve(before, current.id);
    setIndex(nextIndex < 0 ? 0 : nextIndex);
    setFocusToken((token) => token + 1);
  }

  function onUndo() {
    const id = review.undo();
    if (!id) return;
    setMode("cards");
    setRestoreId(id);
    setFocusToken((token) => token + 1);
  }

  const frameStyle = wide ? styles.wideFrame : styles.frame;
  const confirmCopy = current && confirm ? confirmationCopy(current, confirm) : null;
  const caughtUpHint =
    snoozedCount === 1
      ? "1 snoozed request will come back later."
      : snoozedCount > 1
        ? `${snoozedCount} snoozed requests will come back later.`
        : "New requests will show up here.";

  return (
    <SafeAreaView edges={["top", "left", "right"]} style={styles.safe}>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={[styles.header, frameStyle, wide && styles.wideCenter]}>
          <View style={styles.titleRow} accessibilityRole="header" accessibilityLabel="Needs you">
            <View style={styles.segment} accessibilityRole="tablist">
              <Segment
                label="Pending"
                selected={mode !== "reviewed"}
                onPress={() => setMode((value) => (value === "reviewed" ? "cards" : value))}
              />
              <Segment label="Reviewed" selected={mode === "reviewed"} onPress={() => setMode("reviewed")} />
            </View>
            <View style={styles.viewToggle} accessibilityRole="tablist">
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Show cards"
                accessibilityState={{ selected: mode === "cards" }}
                onPress={() => setMode("cards")}
                style={[styles.viewButton, mode === "cards" && styles.viewButtonOn]}
              >
                <LayoutIcon kind="card" color={mode === "cards" ? colors.accent : colors.muted} />
              </Pressable>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Show list"
                accessibilityState={{ selected: mode === "list" }}
                onPress={() => setMode("list")}
                style={[styles.viewButton, mode === "list" && styles.viewButtonOn]}
              >
                <LayoutIcon kind="list" color={mode === "list" ? colors.accent : colors.muted} />
              </Pressable>
            </View>
          </View>
          {ready && mode === "cards" && pending.length > 0 ? (
            <View style={styles.pager}>
              <ArrowButton
                label="Previous request"
                glyph="‹"
                disabled={index <= 0 || Boolean(busyId)}
                onPress={() => setIndex((value) => browseTo(value, -1, pending.length))}
              />
              <Text style={styles.position} accessibilityLiveRegion={Platform.OS === "web" ? "polite" : "none"}>
                {Math.min(index, pending.length - 1) + 1} of {pending.length}
              </Text>
              <ArrowButton
                label="Next request"
                glyph="›"
                disabled={index >= pending.length - 1 || Boolean(busyId)}
                onPress={() => setIndex((value) => browseTo(value, 1, pending.length))}
              />
            </View>
          ) : null}
        </View>

        {notice ? (
          <View style={[styles.notice, frameStyle]} accessibilityLiveRegion={Platform.OS === "web" ? "polite" : "none"}>
            <Text style={styles.noticeText}>{notice}</Text>
            <View style={styles.noticeActions}>
              {canUndo ? (
                <Pressable accessibilityRole="button" disabled={Boolean(busyId)} onPress={onUndo} hitSlop={8}>
                  <Text style={styles.noticeAction}>Undo</Text>
                </Pressable>
              ) : null}
              <Pressable accessibilityRole="button" accessibilityLabel="Dismiss confirmation" onPress={review.dismissNotice} hitSlop={8}>
                <Text style={styles.noticeDismiss}>Dismiss</Text>
              </Pressable>
            </View>
          </View>
        ) : null}
        {error ? (
          <Text style={[styles.error, frameStyle]} accessibilityRole="alert">
            {error}
          </Text>
        ) : null}

        <View
          style={[styles.stage, wide && { width: layout.pagerWidth, alignSelf: "center" }]}
          onLayout={(event) => setStageHeight(event.nativeEvent.layout.height)}
        >
          {!ready ? <LoadingState label="Loading requests…" /> : null}
          {ready && loadError ? (
            <View style={styles.stateBlock}>
              <Text style={styles.stateTitle} accessibilityRole="header">
                Couldn’t load requests
              </Text>
              <Text style={styles.stateCopy}>{loadError}</Text>
              <Pressable accessibilityRole="button" onPress={review.retry} style={styles.primary}>
                <Text style={styles.primaryText}>Try again</Text>
              </Pressable>
            </View>
          ) : null}
          {ready && !loadError && mode === "cards" && pending.length === 0 ? (
            <View ref={headingRef} accessible accessibilityRole="header" accessibilityLabel="You're all caught up.">
              <Empty title="You're all caught up." hint={caughtUpHint} />
            </View>
          ) : null}
          {ready && !loadError && mode === "list" ? (
            <ScrollView
              contentContainerStyle={[styles.listPad, { paddingBottom: 32 + insets.bottom }]}
              keyboardShouldPersistTaps="handled"
              accessibilityLabel="Pending"
            >
              <View ref={headingRef} accessible accessibilityRole="header" accessibilityLabel="Pending" style={styles.srOnly} />
              {pending.map((item) => (
                <ListButton
                  key={item.id}
                  item={item}
                  now={now}
                  onPress={() => {
                    const next = pending.findIndex((entry) => entry.id === item.id);
                    setIndex(Math.max(0, next));
                    setMode("cards");
                  }}
                />
              ))}
              {pending.length === 0 ? <Empty title="You're all caught up." hint={caughtUpHint} /> : null}
            </ScrollView>
          ) : null}
          {ready && !loadError && mode === "reviewed" ? (
            <ScrollView contentContainerStyle={[styles.listPad, { paddingBottom: 24 + insets.bottom }]} accessibilityLabel="Reviewed">
              <Text style={styles.srOnly} accessibilityRole="header">
                Reviewed
              </Text>
              {reviewed.length === 0 ? <Empty title="Nothing reviewed yet." hint="Decisions you make will be listed here." /> : null}
              {reviewed.map((item) => (
                <View key={item.id} style={styles.reviewed}>
                  <Text style={styles.reviewedWho}>{item.requester.name}</Text>
                  <Text style={[styles.outcome, outcomeStyle(item.resolution?.outcome)]}>{item.resolution?.label}</Text>
                  <Text style={styles.meta}>{item.resolution ? formatDateTime(new Date(item.resolution.decidedAt)) : ""}</Text>
                  <Text style={styles.body}>{item.resolution?.detail}</Text>
                </View>
              ))}
            </ScrollView>
          ) : null}
          {ready && !loadError && mode === "cards" && pending.length > 0 && stageHeight > 0 ? (
            <ScrollView
              ref={scroller}
              horizontal
              showsHorizontalScrollIndicator={false}
              scrollEnabled={browsingEnabled(Boolean(busyId) || changesOpen || snoozeOpen || confirm !== null) && pending.length > 1}
              nestedScrollEnabled
              directionalLockEnabled
              snapToInterval={layout.cardWidth + layout.gap}
              snapToAlignment="start"
              disableIntervalMomentum
              decelerationRate="fast"
              contentContainerStyle={{ paddingHorizontal: layout.side }}
              onMomentumScrollEnd={(event) => settle(event.nativeEvent.contentOffset.x)}
              onScrollEndDrag={(event: NativeSyntheticEvent<NativeScrollEvent>) => settle(event.nativeEvent.contentOffset.x)}
              style={{ height: stageHeight }}
            >
              {pending.map((item, itemIndex) => (
                <View
                  key={item.id}
                  style={{ width: layout.cardWidth, height: stageHeight, marginRight: itemIndex === pending.length - 1 ? 0 : layout.gap }}
                  accessibilityElementsHidden={itemIndex !== index}
                  importantForAccessibility={itemIndex === index ? "yes" : "no-hide-descendants"}
                >
                  <View style={[styles.card, !wide && styles.cardFull, isExpired(item, now) && styles.cardExpired, busyId === item.id && styles.cardBusy]}>
                    <ScrollView
                      nestedScrollEnabled
                      keyboardShouldPersistTaps="handled"
                      automaticallyAdjustKeyboardInsets
                      contentContainerStyle={styles.cardPad}
                      style={styles.flex}
                    >
                      <CardBody
                        item={item}
                        now={now}
                        open={open}
                        onToggle={toggle}
                        headingRef={itemIndex === index ? headingRef : undefined}
                      />
                    </ScrollView>
                    <View style={styles.actions}>
                      <DecisionActions
                        item={item}
                        now={now}
                        busy={busyId === item.id}
                        activeAction={busyId === item.id ? activeAction : null}
                        changesOpen={itemIndex === index && changesOpen}
                        snoozeOpen={itemIndex === index && snoozeOpen}
                        onPrimary={() => onPrimary(item)}
                        onDecide={(action) => void onDecide(action)}
                        onEdit={() => router.push({ pathname: "/(app)/review/edit", params: { id: item.id } })}
                        onOpenChanges={() => {
                          setSnoozeOpen(false);
                          setChangesOpen(true);
                        }}
                        onCloseChanges={() => setChangesOpen(false)}
                        onToggleSnooze={() => {
                          setChangesOpen(false);
                          setSnoozeOpen((value) => !value);
                        }}
                        onSnooze={onSnooze}
                        onFeedback={(text) => review.setFeedback(item.id, text)}
                      />
                    </View>
                  </View>
                </View>
              ))}
            </ScrollView>
          ) : null}
        </View>
      </KeyboardAvoidingView>
      <Modal visible={confirm !== null} transparent animationType={reduceMotion ? "none" : "fade"} onRequestClose={() => setConfirm(null)}>
        <View style={styles.modalBackdrop}>
          <View style={styles.sheet} accessibilityViewIsModal>
            <Text style={styles.sheetTitle}>{confirmCopy?.title}</Text>
            <Text style={styles.sheetBody}>{confirmCopy?.body}</Text>
            <Pressable
              accessibilityRole="button"
              disabled={Boolean(busyId)}
              onPress={() => confirm && void onDecide(confirm)}
              style={[styles.primary, busyId && styles.disabled]}
            >
              {busyId ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryText}>{confirmCopy?.confirm}</Text>}
            </Pressable>
            <Pressable accessibilityRole="button" disabled={Boolean(busyId)} onPress={() => setConfirm(null)} style={styles.secondary}>
              <Text style={styles.secondaryText}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

function outcomeStyle(outcome?: string) {
  if (outcome === "approved") return styles.outcomeApproved;
  if (outcome === "declined") return styles.outcomeDeclined;
  if (outcome === "changes_requested") return styles.outcomeChanges;
  return styles.outcomeDismissed;
}

function LoadingState({ label }: { label: string }) {
  return (
    <View style={styles.stateBlock} accessibilityRole="progressbar" accessibilityLabel={label}>
      <ActivityIndicator color={colors.accent} />
      <Text style={styles.stateCopy}>{label}</Text>
    </View>
  );
}

function Segment({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="tab"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={[styles.segmentButton, selected && styles.segmentOn]}
    >
      <Text style={[styles.segmentText, selected && styles.segmentTextOn]}>{label}</Text>
    </Pressable>
  );
}

function ArrowButton({ label, glyph, disabled, onPress }: { label: string; glyph: string; disabled?: boolean; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: Boolean(disabled) }}
      disabled={disabled}
      onPress={onPress}
      hitSlop={6}
      style={[styles.arrow, disabled && styles.disabled]}
    >
      <Text style={styles.arrowGlyph}>{glyph}</Text>
    </Pressable>
  );
}

function ListButton({ item, now, onPress }: { item: ReviewItem; now: Date; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.listRow}>
      <Avatar name={item.requester.name} size={36} />
      <View style={styles.listBody}>
        <Text style={styles.listTitle}>{item.headline}</Text>
        <Text style={styles.meta}>
          {item.requester.name} · {statusLabel(item, now)} · {formatRequested(item.requestedAt, now)}
        </Text>
      </View>
    </Pressable>
  );
}

function CardBody({
  item,
  now,
  open,
  onToggle,
  headingRef,
}: {
  item: ReviewItem;
  now: Date;
  open: Record<string, boolean>;
  onToggle: (key: string) => void;
  headingRef?: Ref<ComponentRef<typeof View>>;
}) {
  const { selectOption } = useReview();
  const expired = isExpired(item, now);
  const status = statusLabel(item, now);
  const statusText = item.timeSensitive && !expired ? `${status} · Time sensitive` : status;
  return (
    <View style={styles.cardBody}>
      <View style={styles.who}>
        <Avatar name={item.requester.name} size={36} />
        <View style={styles.whoText}>
          <Text style={styles.requester}>{item.requester.name}</Text>
          <Text style={styles.meta}>{kindLabel(item.requester.kind)}</Text>
        </View>
        <Text style={styles.time}>{formatRequested(item.requestedAt, now)}</Text>
      </View>
      <Text style={[styles.status, expired && styles.statusExpired]}>{statusText}</Text>
      <View ref={headingRef} accessible accessibilityRole="header" accessibilityLabel={item.headline}>
        <Text style={styles.headline}>{item.headline}</Text>
      </View>
      <Text style={styles.body}>{item.explanation}</Text>
      <View style={styles.summary}>
        <Fact label="Evidence" value={item.summary.evidence} />
        <Fact label="Proposed action" value={item.summary.proposed} />
        <Fact label="Consequences" value={item.summary.consequences} />
      </View>
      {expired ? <Text style={styles.expiredCopy}>{expirationCopy(item, now)}</Text> : null}
      {item.kind === "work_review" ? <PlanList item={item} /> : null}
      {item.kind === "outgoing_email" && item.draft ? (
        <EmailPreview item={item} open={Boolean(open[`${item.id}:message`])} onToggle={onToggle} />
      ) : null}
      {item.kind === "appointment" ? (
        <View accessibilityRole="radiogroup" style={styles.choices}>
          <Text style={styles.factLabel}>Choose a time</Text>
          {item.options.map((option) => {
            const selected = item.selectedOptionId === option.id;
            return (
              <Pressable
                key={option.id}
                accessibilityRole="radio"
                accessibilityState={{ selected }}
                onPress={() => selectOption(item.id, option.id)}
                style={[styles.choice, selected && styles.choiceOn]}
              >
                <Text style={styles.choiceLabel}>{option.label}</Text>
                <Text style={styles.meta}>{option.detail}</Text>
              </Pressable>
            );
          })}
        </View>
      ) : null}
      {item.details.map((detail) => (
        <Disclosure
          key={detail.id}
          label={detail.title}
          open={Boolean(open[`${item.id}:${detail.id}`])}
          onPress={() => onToggle(`${item.id}:${detail.id}`)}
          body={detail.body}
        />
      ))}
    </View>
  );
}

function PlanList({ item }: { item: ReviewItem }) {
  return (
    <View style={styles.plans}>
      <Text style={styles.factLabel}>Comparison</Text>
      {item.recommendation ? <Text style={styles.body}>{item.recommendation}</Text> : null}
      {item.plans.map((plan) => (
        <View key={plan.id} style={styles.plan}>
          <View style={styles.planTop}>
            <Text style={styles.planName}>{plan.name}</Text>
            {plan.current ? <Text style={styles.planCurrent}>Current</Text> : null}
          </View>
          <Text style={styles.meta}>
            {plan.premium} · {plan.deductible} deductible
          </Text>
          <Text style={styles.meta}>
            Rental {plan.rental} · Glass {plan.windshield} · Roadside {plan.roadside}
          </Text>
          {plan.tradeoff ? <Text style={styles.planTradeoff}>{plan.tradeoff}</Text> : null}
        </View>
      ))}
    </View>
  );
}

function EmailPreview({ item, open, onToggle }: { item: ReviewItem; open: boolean; onToggle: (key: string) => void }) {
  const draft = item.draft;
  const [file, setFile] = useState<string | null>(null);
  if (!draft) return null;
  const preview = draft.body.length > 220 && !open ? `${draft.body.slice(0, 220).trim()}…` : draft.body;
  const selected = draft.attachments.find((entry) => entry.id === file);
  return (
    <View style={styles.block}>
      <Fact label="To" value={`${draft.toName} · ${draft.toAddress}`} />
      <Fact label="Subject" value={draft.subject} />
      <Text style={styles.body}>{preview}</Text>
      {draft.body.length > 220 ? (
        <Pressable accessibilityRole="button" onPress={() => onToggle(`${item.id}:message`)}>
          <Text style={styles.link}>{open ? "Show less" : "Read full message"}</Text>
        </Pressable>
      ) : null}
      {draft.attachments.map((attachment) => (
        <Pressable
          key={attachment.id}
          accessibilityRole="button"
          accessibilityLabel={`${attachment.name}, ${attachment.kindLabel}, ${attachment.sizeLabel}`}
          onPress={() => setFile((current) => (current === attachment.id ? null : attachment.id))}
          style={styles.file}
        >
          <Text style={styles.choiceLabel}>{attachment.name}</Text>
          <Text style={styles.meta}>
            {attachment.kindLabel} · {attachment.sizeLabel}
          </Text>
        </Pressable>
      ))}
      {selected ? (
        <View style={styles.fileBody}>
          <Text style={styles.factLabel}>{selected.name}</Text>
          <Text style={styles.body}>{selected.preview}</Text>
        </View>
      ) : null}
    </View>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.fact}>
      <Text style={styles.factLabel}>{label}</Text>
      <Text style={styles.factValue}>{value}</Text>
    </View>
  );
}

function Disclosure({ label, open, onPress, body }: { label: string; open: boolean; onPress: () => void; body: string }) {
  return (
    <View>
      <Pressable accessibilityRole="button" accessibilityState={{ expanded: open }} onPress={onPress} style={styles.linkHit}>
        <Text style={styles.link}>{open ? `Hide ${label.toLowerCase()}` : label}</Text>
      </Pressable>
      {open ? <Text style={styles.body}>{body}</Text> : null}
    </View>
  );
}

function DecisionActions({
  item,
  now,
  busy,
  activeAction,
  changesOpen,
  snoozeOpen,
  onPrimary,
  onDecide,
  onEdit,
  onOpenChanges,
  onCloseChanges,
  onToggleSnooze,
  onSnooze,
  onFeedback,
}: {
  item: ReviewItem;
  now: Date;
  busy: boolean;
  activeAction: DecisionAction | null;
  changesOpen: boolean;
  snoozeOpen: boolean;
  onPrimary: () => void;
  onDecide: (action: DecisionAction) => void;
  onEdit: () => void;
  onOpenChanges: () => void;
  onCloseChanges: () => void;
  onToggleSnooze: () => void;
  onSnooze: (choice: SnoozeChoice | "next") => void;
  onFeedback: (text: string) => void;
}) {
  const expired = isExpired(item, now);
  const action = primaryAction(item, now);
  const needsTime = item.kind === "appointment" && !item.selectedOptionId;
  const primaryBusy = busy && activeAction === action;
  const primaryText = primaryBusy ? busyLabel(action) : actionLabel(action);
  return (
    <View style={styles.actionStack}>
      <Text style={styles.authorize}>{authorizationCopy(item, now)}</Text>
      {changesOpen ? (
        <FeedbackBox
          value={item.feedback}
          disabled={busy}
          sending={activeAction === "request_changes"}
          onChange={onFeedback}
          onSend={() => onDecide("request_changes")}
          onCancel={onCloseChanges}
        />
      ) : (
        <>
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: busy || needsTime, busy: primaryBusy }}
            accessibilityHint={needsTime ? "Choose a time first." : authorizationCopy(item, now)}
            disabled={busy || needsTime}
            onPress={onPrimary}
            style={[styles.primary, (busy || needsTime) && styles.disabled]}
          >
            <Text style={styles.primaryText}>{primaryText}</Text>
          </Pressable>
          {needsTime ? <Text style={styles.hint}>Choose a time first.</Text> : null}
          {!expired && offersChanges(item) ? (
            <Pressable accessibilityRole="button" disabled={busy} onPress={onOpenChanges} style={[styles.secondary, busy && styles.disabled]}>
              <Text style={styles.secondaryText}>Request changes</Text>
            </Pressable>
          ) : null}
          <View style={styles.tertiaryRow}>
            {!expired ? (
              <Pressable accessibilityRole="button" disabled={busy} onPress={onToggleSnooze} style={styles.tertiary}>
                <Text style={styles.tertiaryText}>Later</Text>
              </Pressable>
            ) : null}
            {item.kind === "document_access" && !expired ? (
              <Pressable accessibilityRole="button" disabled={busy} onPress={() => onDecide("decline")} style={styles.tertiary}>
                <Text style={styles.dangerText}>{activeAction === "decline" ? busyLabel("decline") : "Decline"}</Text>
              </Pressable>
            ) : null}
            {item.kind === "device_authorization" && !expired ? (
              <Pressable accessibilityRole="button" disabled={busy} onPress={() => onDecide("deny_device")} style={styles.tertiary}>
                <Text style={styles.dangerText}>{activeAction === "deny_device" ? busyLabel("deny_device") : "Deny"}</Text>
              </Pressable>
            ) : null}
            {item.kind === "outgoing_email" ? (
              <Pressable accessibilityRole="button" disabled={busy} onPress={onEdit} style={styles.tertiary}>
                <Text style={styles.tertiaryText}>Edit message</Text>
              </Pressable>
            ) : null}
          </View>
          {snoozeOpen ? (
            <View style={styles.snooze} accessibilityRole="menu">
              <SnoozeChoiceButton label="Show next" onPress={() => onSnooze("next")} />
              <SnoozeChoiceButton label="In 1 hour" onPress={() => onSnooze("hour")} />
              <SnoozeChoiceButton label="This evening" onPress={() => onSnooze("evening")} />
              <SnoozeChoiceButton label="Tomorrow morning" onPress={() => onSnooze("tomorrow")} />
              <Pressable accessibilityRole="button" onPress={onToggleSnooze} style={styles.tertiary}>
                <Text style={styles.tertiaryText}>Cancel</Text>
              </Pressable>
            </View>
          ) : null}
        </>
      )}
    </View>
  );
}

function SnoozeChoiceButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={styles.snoozeChoice}>
      <Text style={styles.snoozeText}>{label}</Text>
    </Pressable>
  );
}

function FeedbackBox({
  value,
  disabled,
  sending,
  onChange,
  onSend,
  onCancel,
}: {
  value: string;
  disabled: boolean;
  sending: boolean;
  onChange: (text: string) => void;
  onSend: () => void;
  onCancel: () => void;
}) {
  return (
    <View style={styles.feedback}>
      <Text style={styles.factLabel}>What should change?</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        editable={!disabled}
        multiline
        placeholder="Add a short note"
        placeholderTextColor={colors.muted}
        accessibilityLabel="What should change?"
        style={styles.input}
      />
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ disabled: disabled || !value.trim(), busy: sending }}
        disabled={disabled || !value.trim()}
        onPress={onSend}
        style={[styles.primary, (disabled || !value.trim()) && styles.disabled]}
      >
        <Text style={styles.primaryText}>{sending ? busyLabel("request_changes") : "Send note"}</Text>
      </Pressable>
      <Pressable accessibilityRole="button" disabled={disabled} onPress={onCancel} style={styles.tertiary}>
        <Text style={styles.tertiaryText}>Cancel</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  flex: { flex: 1 },
  frame: { paddingHorizontal: 16 },
  wideFrame: { paddingHorizontal: 0 },
  wideCenter: { alignSelf: "center", width: 640 },
  header: { paddingTop: 8, paddingBottom: 4, gap: 10 },
  titleRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 12 },
  viewToggle: { flexDirection: "row", alignItems: "center", gap: 2, backgroundColor: "#e8eaed", borderRadius: 10, padding: 2 },
  viewButton: { width: 36, height: 36, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  viewButtonOn: { backgroundColor: colors.surface },
  segment: {
    flexDirection: "row",
    alignSelf: "flex-start",
    backgroundColor: "#e8eaed",
    borderRadius: 10,
    padding: 2,
    gap: 2,
  },
  segmentButton: { minHeight: 32, paddingHorizontal: 12, borderRadius: 8, alignItems: "center", justifyContent: "center" },
  segmentOn: { backgroundColor: colors.surface },
  segmentText: { color: colors.muted, fontSize: 13, fontWeight: "600" },
  segmentTextOn: { color: colors.text },
  pager: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  arrow: { minWidth: 44, minHeight: 36, alignItems: "center", justifyContent: "center" },
  arrowGlyph: { color: colors.accent, fontSize: 22, fontWeight: "500", lineHeight: 26 },
  position: { color: colors.muted, fontSize: 13, fontWeight: "500" },
  notice: {
    marginTop: 8,
    marginHorizontal: 16,
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    paddingHorizontal: 12,
    paddingVertical: 10,
    gap: 8,
  },
  noticeText: { color: colors.text, fontSize: 14, lineHeight: 20 },
  noticeActions: { flexDirection: "row", gap: 16 },
  noticeAction: { color: colors.accent, fontWeight: "600", fontSize: 14 },
  noticeDismiss: { color: colors.muted, fontWeight: "600", fontSize: 14 },
  error: { color: colors.danger, paddingHorizontal: 20, paddingTop: 8, fontSize: 14, lineHeight: 20 },
  stage: { flex: 1, minHeight: 0, marginTop: 8 },
  stateBlock: { padding: 24, gap: 12, alignItems: "flex-start" },
  stateTitle: { color: colors.text, fontSize: 18, fontWeight: "600" },
  stateCopy: { color: colors.muted, fontSize: 15, lineHeight: 21 },
  card: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    overflow: "hidden",
    shadowColor: "#202124",
    shadowOpacity: 0.06,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  cardFull: {
    borderRadius: 0,
    borderLeftWidth: 0,
    borderRightWidth: 0,
    shadowOpacity: 0,
    elevation: 0,
  },
  cardExpired: { backgroundColor: "#fffdf8" },
  cardBusy: { opacity: 0.9 },
  cardPad: { flexGrow: 1, padding: 16, paddingBottom: 28 },
  cardBody: { gap: 10 },
  who: { flexDirection: "row", gap: 10, alignItems: "center" },
  whoText: { flex: 1, gap: 1 },
  requester: { color: colors.text, fontSize: 15, fontWeight: "600" },
  time: { color: colors.muted, fontSize: 12, flexShrink: 1, textAlign: "right" },
  meta: { color: colors.muted, fontSize: 13, lineHeight: 18 },
  status: {
    alignSelf: "flex-start",
    color: "#174ea6",
    backgroundColor: "#e8f0fe",
    fontWeight: "600",
    fontSize: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    overflow: "hidden",
  },
  statusExpired: { color: "#7a4e00", backgroundColor: "#fef7e0" },
  headline: { color: colors.text, fontSize: 17, fontWeight: "600", lineHeight: 23 },
  body: { color: colors.text, fontSize: 15, lineHeight: 21 },
  summary: { backgroundColor: colors.bg, borderRadius: 12, padding: 12, gap: 10 },
  fact: { gap: 2 },
  factLabel: { color: colors.muted, fontSize: 12, fontWeight: "600" },
  factValue: { color: colors.text, fontSize: 15, lineHeight: 21 },
  expiredCopy: { color: "#7a4e00", fontSize: 14, lineHeight: 20 },
  linkHit: { minHeight: 36, justifyContent: "center" },
  link: { color: colors.accent, fontWeight: "600", fontSize: 15 },
  choices: { gap: 8 },
  choice: { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, borderRadius: 12, padding: 12, gap: 2 },
  choiceOn: { borderColor: colors.accent, backgroundColor: "#e8f0fe" },
  choiceLabel: { color: colors.text, fontWeight: "600", fontSize: 15 },
  block: { gap: 8 },
  plans: { gap: 8 },
  plan: { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, borderRadius: 12, padding: 12, gap: 3 },
  planTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  planName: { color: colors.text, fontWeight: "600", fontSize: 15, flex: 1 },
  planCurrent: { color: "#174ea6", fontSize: 12, fontWeight: "600" },
  planTradeoff: { color: colors.text, fontSize: 13, lineHeight: 18, marginTop: 2 },
  file: { borderWidth: StyleSheet.hairlineWidth, borderColor: colors.border, borderRadius: 12, padding: 12 },
  fileBody: { backgroundColor: colors.bg, borderRadius: 12, padding: 12, gap: 4 },
  actions: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16, backgroundColor: colors.surface },
  actionStack: { gap: 8 },
  authorize: { color: colors.muted, fontSize: 13, lineHeight: 18 },
  primary: {
    minHeight: 48,
    borderRadius: 12,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  primaryText: { color: "#fff", fontWeight: "600", fontSize: 16, textAlign: "center" },
  secondary: {
    minHeight: 44,
    borderRadius: 12,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  secondaryText: { color: colors.text, fontWeight: "600", fontSize: 15, textAlign: "center" },
  tertiaryRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between" },
  tertiary: { minHeight: 44, justifyContent: "center", paddingHorizontal: 4 },
  tertiaryText: { color: colors.muted, fontSize: 15, fontWeight: "600" },
  dangerText: { color: colors.danger, fontSize: 15, fontWeight: "600" },
  hint: { color: colors.muted, fontSize: 13 },
  disabled: { opacity: 0.5 },
  snooze: { backgroundColor: colors.bg, borderRadius: 12, paddingVertical: 4 },
  snoozeChoice: { minHeight: 44, justifyContent: "center", paddingHorizontal: 12 },
  snoozeText: { color: colors.text, fontSize: 15 },
  feedback: { gap: 8 },
  input: {
    minHeight: 72,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    borderRadius: 12,
    padding: 12,
    color: colors.text,
    fontSize: 16,
    textAlignVertical: "top",
    backgroundColor: colors.surface,
  },
  listPad: { paddingBottom: 28 },
  srOnly: { position: "absolute", width: 1, height: 1, overflow: "hidden" },
  listRow: {
    flexDirection: "row",
    gap: 12,
    alignItems: "center",
    backgroundColor: colors.surface,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  listBody: { flex: 1, gap: 2 },
  listTitle: { color: colors.text, fontSize: 15, fontWeight: "600", lineHeight: 20 },
  reviewed: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.border,
    padding: 14,
    gap: 4,
  },
  reviewedWho: { color: colors.text, fontWeight: "600", fontSize: 15 },
  outcome: { fontWeight: "600", fontSize: 14 },
  outcomeApproved: { color: "#188038" },
  outcomeDeclined: { color: colors.danger },
  outcomeChanges: { color: "#174ea6" },
  outcomeDismissed: { color: colors.muted },
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(32, 33, 36, 0.4)",
    justifyContent: "flex-end",
    padding: 16,
  },
  sheet: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 16,
    gap: 12,
    marginBottom: 12,
  },
  sheetTitle: { color: colors.text, fontSize: 18, fontWeight: "600" },
  sheetBody: { color: colors.text, fontSize: 15, lineHeight: 21 },
});
