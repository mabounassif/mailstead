import assert from "node:assert/strict";
import test from "node:test";
import {
  accessName,
  badgeLabel,
  browseMove,
  browsingEnabled,
  createFixtures,
  deckLayout,
  destinationAfterLater,
  expirationCopy,
  formatDateTime,
  indexAfterResolve,
  isActionable,
  isExpired,
  isSnoozed,
  pendingCount,
  performDecision,
  resolveItem,
  slideDecision,
  snoozeDeadline,
  unresolvedItems,
  visiblePending,
  DecisionGate,
} from "./review/queue";
import type { ReviewItem } from "./review/types";

const now = new Date(2026, 9, 25, 15, 0, 0);

function fixtures(): ReviewItem[] {
  return createFixtures(now);
}

test("pending count matches the visible deck, including expired requests", () => {
  const items = fixtures();
  assert.equal(items.length, 6);
  assert.equal(visiblePending(items, now).length, 6);
  assert.equal(pendingCount(items, now), 6);
  assert.equal(badgeLabel(pendingCount(items, now)), "6");
  const expired = items.find((item) => item.id === "invoices-expired");
  assert.ok(expired);
  assert.equal(isExpired(expired, now), true);
  assert.equal(isActionable(expired, now), false);
  assert.equal(expirationCopy(expired, now)?.includes("Approval is turned off"), true);
  const coverage = items.find((item) => item.id === "coverage-comparison");
  assert.equal(coverage?.headline, "Review your insurance options");
});

test("opening a request does not change the badge", () => {
  const items = fixtures();
  const before = pendingCount(items, now);
  const opened = items.map((item) => ({ ...item }));
  assert.equal(pendingCount(opened, now), before);
  assert.equal(unresolvedItems(opened).length, 6);
  assert.equal(visiblePending(opened, now).length, before);
});

test("badge hides at zero and caps at 99+", () => {
  assert.equal(badgeLabel(0), null);
  assert.equal(badgeLabel(1), "1");
  assert.equal(badgeLabel(99), "99");
  assert.equal(badgeLabel(100), "99+");
  assert.equal(accessName(4), "Review queue, 4 pending");
});

test("later moves to another request without resolving it", () => {
  const items = fixtures();
  const ids = unresolvedItems(items).map((item) => item.id);
  assert.deepEqual(destinationAfterLater(ids, ids[0]), { type: "card", id: ids[1] });
  assert.deepEqual(destinationAfterLater([ids[0]], ids[0]), { type: "list" });
  assert.equal(pendingCount(items, now), 6);
  assert.equal(items.every((item) => item.status === "pending"), true);
});

test("browsing only chooses a direction", () => {
  assert.equal(browseMove(12, 0), 0);
  assert.equal(browseMove(-80, 10), 1);
  assert.equal(browseMove(90, 4), -1);
  assert.equal(browseMove(-80, 120), 0);
  assert.equal(browsingEnabled(true), false);
  assert.equal(browsingEnabled(false), true);
});

test("an unfinished slide resets and a completed slide commits", () => {
  assert.equal(slideDecision(0), "reset");
  assert.equal(slideDecision(0.91), "reset");
  assert.equal(slideDecision(0.92), "commit");
  assert.equal(slideDecision(1), "commit");
});

test("allowing the tax folder records a 24 hour read and blocks a second decision", () => {
  const tax = fixtures()[0];
  const result = resolveItem(tax, "allow_24h", now);
  assert.equal(result.ok, true);
  if (!result.ok) return;
  const end = new Date(now.getTime() + 24 * 60 * 60 * 1000);
  assert.match(result.item.resolution?.detail ?? "", /2026 Taxes/);
  assert.match(result.item.resolution?.detail ?? "", new RegExp(formatDateTime(end).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  assert.match(result.item.resolution?.detail ?? "", /separate approval/);
  assert.equal(result.item.status, "resolved");
  const again = resolveItem(result.item, "allow_24h", now);
  assert.equal(again.ok, false);
  const next = fixtures().map((item) => (item.id === tax.id ? result.item : item));
  assert.equal(pendingCount(next, now), 5);
});

test("sending uses the edited message and does not offer another send", () => {
  const email = fixtures().find((item) => item.id === "accountant-reply");
  assert.ok(email?.draft);
  const edited = {
    ...email,
    draft: { ...email.draft, subject: "Updated payment note", body: "Sending the revised note." },
  };
  const result = resolveItem(edited, "approve_send", now);
  assert.equal(result.ok, true);
  if (!result.ok) return;
  assert.match(result.item.resolution?.detail ?? "", /Updated payment note/);
  assert.match(result.confirmation, /Priya Shah/);
  assert.equal(result.item.resolution?.label, "Approved to send");
  assert.match(result.confirmation, /No email was sent/);
  const empty = resolveItem({ ...email, draft: { ...email.draft, body: "  " } }, "approve_send", now);
  assert.equal(empty.ok, false);
  if (!empty.ok) assert.equal(empty.reason, "empty_message");
});

test("confirming a time requires a choice", () => {
  const item = fixtures().find((entry) => entry.id === "harbor-service");
  assert.ok(item);
  const blocked = resolveItem(item, "confirm_time", now);
  assert.equal(blocked.ok, false);
  if (!blocked.ok) assert.equal(blocked.reason, "missing_choice");
  const chosen = { ...item, selectedOptionId: item.options[1].id };
  const result = resolveItem(chosen, "confirm_time", now);
  assert.equal(result.ok, true);
  if (result.ok) assert.match(result.item.resolution?.detail ?? "", /No repair was approved/);
});

test("marking insurance reviewed does not purchase or change a policy", () => {
  const item = fixtures().find((entry) => entry.id === "coverage-comparison");
  assert.ok(item);
  const missing = resolveItem(item, "request_changes", now);
  assert.equal(missing.ok, false);
  const noted = resolveItem({ ...item, feedback: "Please add roadside coverage." }, "request_changes", now);
  assert.equal(noted.ok, true);
  if (noted.ok) assert.match(noted.item.resolution?.detail ?? "", /roadside coverage/);
  const accepted = resolveItem(item, "mark_reviewed", now);
  assert.equal(accepted.ok, true);
  if (accepted.ok) assert.match(accepted.confirmation, /No insurance was purchased or changed/);
});

test("device access can be allowed or denied, and expired approval is refused", async () => {
  const device = fixtures().find((item) => item.id === "pixel-tablet");
  assert.ok(device);
  const denied = resolveItem(device, "deny_device", now);
  assert.equal(denied.ok, true);
  if (denied.ok) assert.equal(denied.item.resolution?.outcome, "declined");
  let reads = 0;
  const expired = await performDecision(device, "allow_device", {
    delayMs: 5,
    clock: () => {
      reads += 1;
      return reads === 1 ? now : new Date(device.expiresAt ?? now);
    },
  });
  assert.equal(expired.ok, false);
  if (!expired.ok) assert.equal(expired.reason, "expired");
  assert.equal(device.status, "pending");
});

test("dismissing an expired request removes it from the pending count", () => {
  const items = fixtures();
  const expired = items.find((item) => item.id === "invoices-expired");
  assert.ok(expired);
  const blocked = resolveItem(expired, "allow_24h", now);
  assert.equal(blocked.ok, false);
  const dismissed = resolveItem(expired, "dismiss_expired", now);
  assert.equal(dismissed.ok, true);
  if (!dismissed.ok) return;
  const next = items.map((item) => (item.id === expired.id ? dismissed.item : item));
  assert.equal(pendingCount(next, now), 5);
  assert.equal(visiblePending(next, now).length, pendingCount(next, now));
  assert.equal(dismissed.item.resolution?.outcome, "dismissed");
});

test("a second decision is ignored while one is processing", () => {
  const gate = new DecisionGate();
  assert.equal(gate.tryBegin(), true);
  assert.equal(gate.tryBegin(), false);
  gate.end();
  assert.equal(gate.tryBegin(), true);
});

test("resolving a card reveals the next pending index", () => {
  assert.equal(indexAfterResolve(["a", "b", "c"], "a"), 0);
  assert.equal(indexAfterResolve(["a", "b", "c"], "b"), 1);
  assert.equal(indexAfterResolve(["a", "b", "c"], "c"), 1);
  assert.equal(indexAfterResolve(["a"], "a"), -1);
});

test("phone layout gives the active card the full width", () => {
  const phone = deckLayout(390);
  assert.equal(phone.cardWidth, 390);
  assert.equal(phone.side, 0);
  assert.equal(phone.gap, 0);
  const wide = deckLayout(1280);
  assert.equal(wide.cardWidth, 640);
  assert.equal(wide.gap, 0);
  assert.equal(wide.pagerWidth, 640);
});

test("snooze hides a request until the deadline and does not resolve it", () => {
  const items = fixtures();
  const first = items[0];
  const until = snoozeDeadline("hour", now);
  const snoozed = items.map((item) => (item.id === first.id ? { ...item, snoozeUntil: until.toISOString() } : item));
  assert.equal(isSnoozed(snoozed[0], now), true);
  assert.equal(pendingCount(snoozed, now), 5);
  assert.equal(visiblePending(snoozed, now).some((item) => item.id === first.id), false);
  assert.equal(snoozed[0].status, "pending");
  assert.equal(isSnoozed(snoozed[0], new Date(until.getTime() + 1000)), false);
});

test("only the appointment and the device are marked time sensitive", () => {
  const flagged = fixtures()
    .filter((item) => item.timeSensitive)
    .map((item) => item.id)
    .sort();
  assert.deepEqual(flagged, ["harbor-service", "pixel-tablet"]);
});
