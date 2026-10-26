const assert = require("node:assert/strict");
const test = require("node:test");
const Q = require("./review_queue.js");

const now = new Date(2026, 9, 25, 15, 0, 0);

test("pending count matches the visible deck and caps at 99+", () => {
  const items = Q.createFixtures(now);
  assert.equal(items.length, 6);
  assert.equal(Q.visiblePending(items, now).length, 6);
  assert.equal(Q.pendingCount(items, now), 6);
  assert.equal(items.find((item) => item.id === "coverage-comparison").headline, "Review your insurance options");
  assert.equal(Q.badgeLabel(0), null);
  assert.equal(Q.badgeLabel(100), "99+");
  assert.equal(Q.accessName(5), "Review queue, 5 pending");
});

test("later and reading do not resolve a request", () => {
  const items = Q.createFixtures(now);
  const ids = Q.unresolvedItems(items).map((item) => item.id);
  assert.deepEqual(Q.destinationAfterLater(ids, ids[0]), { type: "card", id: ids[1] });
  assert.deepEqual(Q.destinationAfterLater([ids[0]], ids[0]), { type: "list" });
  assert.equal(items.every((item) => item.status === "pending"), true);
});

test("slide release resets until the gesture is complete", () => {
  assert.equal(Q.slideDecision(0.91), "reset");
  assert.equal(Q.slideDecision(0.92), "commit");
  assert.equal(Q.browsingEnabled(true), false);
});

test("decisions match the request and expired approval is refused", () => {
  const items = Q.createFixtures(now);
  const tax = items[0];
  const allowed = Q.resolveItem(tax, "allow_24h", now);
  assert.equal(allowed.ok, true);
  assert.match(allowed.item.resolution.detail, /2026 Taxes/);
  assert.match(allowed.item.resolution.detail, /separate approval/);
  const email = items.find((item) => item.id === "accountant-reply");
  const edited = { ...email, draft: { ...email.draft, subject: "Updated payment note" } };
  const sent = Q.resolveItem(edited, "approve_send", now);
  assert.match(sent.item.resolution.detail, /Updated payment note/);
  const visit = items.find((item) => item.id === "harbor-service");
  assert.equal(Q.resolveItem(visit, "confirm_time", now).reason, "missing_choice");
  const coverage = items.find((item) => item.id === "coverage-comparison");
  const accepted = Q.resolveItem(coverage, "mark_reviewed", now);
  assert.match(accepted.confirmation, /No insurance was purchased or changed/);
  const expired = items.find((item) => item.id === "invoices-expired");
  assert.equal(Q.resolveItem(expired, "allow_24h", now).reason, "expired");
  const dismissed = Q.resolveItem(expired, "dismiss_expired", now);
  assert.equal(dismissed.item.resolution.outcome, "dismissed");
  const next = items.map((item) => (item.id === expired.id ? dismissed.item : item));
  assert.equal(Q.pendingCount(next, now), 5);
  assert.equal(Q.visiblePending(next, now).length, Q.pendingCount(next, now));
});

test("a device decision is rechecked against the current time", () => {
  const device = Q.createFixtures(now).find((item) => item.id === "pixel-tablet");
  const denied = Q.resolveItem(device, "deny_device", now);
  assert.equal(denied.item.resolution.outcome, "declined");
  const tooLate = new Date(device.expiresAt);
  assert.equal(Q.resolveItem(device, "allow_device", tooLate).reason, "expired");
  assert.equal(device.status, "pending");
});
