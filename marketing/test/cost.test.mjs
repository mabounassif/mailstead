import assert from "node:assert/strict";
import test from "node:test";
import { railway, resend } from "../src/data/pricing.mjs";
import {
  estimate,
  hostingCents,
  incrementalHostingCents,
  overageCents,
  selectResend,
} from "../src/lib/cost.mjs";

test("hobby included credit is not charged twice", () => {
  const hobby = railway.plans.hobby;
  assert.equal(hostingCents(0, hobby), 500);
  assert.equal(hostingCents(5, hobby), 500);
  assert.equal(hostingCents(7.5, hobby), 750);
});

test("incremental hosting uses unused credit only", () => {
  assert.equal(incrementalHostingCents(2, 5), 0);
  assert.equal(incrementalHostingCents(8, 5), 300);
  assert.equal(incrementalHostingCents(5, 0), 500);
});

test("free resend covers 3000 when the daily peak is within 100", () => {
  const fit = selectResend(3000, 100);
  assert.equal(fit.ok, true);
  assert.equal(fit.plan.id, "free");
  assert.equal(fit.feeCents, 0);
});

test("one message over the free monthly quota selects Pro 50k", () => {
  const fit = selectResend(3001, 50);
  assert.equal(fit.plan.id, "pro-50k");
  assert.equal(fit.feeCents, 2000);
});

test("daily peak above 100 moves a small month from Free to Pro", () => {
  const fit = selectResend(1000, 101);
  assert.equal(fit.ok, true);
  assert.equal(fit.plan.id, "pro-50k");
  assert.equal(fit.feeCents, 2000);
  assert.equal(fit.reason, "daily-limit");
});

test("overage is billed in 1000-email buckets and is not the default plan choice", () => {
  const pro = resend.plans.find((plan) => plan.id === "pro-50k");
  assert.equal(overageCents(50000, pro), 0);
  assert.equal(overageCents(50001, pro), 90);
  assert.equal(overageCents(51000, pro), 90);
  const selected = selectResend(50001, 10);
  assert.equal(selected.plan.id, "pro-100k");
  assert.equal(selected.feeCents, 3500);
});

test("annual domain cost is amortized monthly and stays in USD", () => {
  const result = estimate({
    mailboxes: 10,
    messages: 2000,
    dailyPeak: 80,
    hostingPlan: "hobby",
    hostingUsageUsd: 4,
    domainAnnualUsd: 18,
    backupsMonthlyUsd: 0,
    alreadyHosting: false,
  });
  assert.equal(result.domainCents, 150);
  assert.equal(result.standaloneHostingCents, 500);
  assert.equal(result.provider.feeCents, 0);
  assert.equal(result.standaloneTotalCents, 650);
  assert.equal(result.currency, "USD");
});

test("existing hobby allowance can make incremental hosting zero without erasing resend", () => {
  const quiet = estimate({
    mailboxes: 5,
    messages: 400,
    dailyPeak: 20,
    hostingUsageUsd: 1.5,
    unusedCreditUsd: 5,
    alreadyHosting: true,
    domainAnnualUsd: 0,
  });
  assert.equal(quiet.incrementalHostingCents, 0);
  assert.equal(quiet.standaloneHostingCents, 500);
  assert.equal(quiet.incrementalTotalCents, 0);
  assert.equal(quiet.standaloneTotalCents, 500);

  const busy = estimate({
    mailboxes: 50,
    messages: 8000,
    dailyPeak: 400,
    hostingUsageUsd: 1.5,
    unusedCreditUsd: 5,
    alreadyHosting: true,
  });
  assert.equal(busy.provider.plan.id, "pro-50k");
  assert.equal(busy.incrementalHostingCents, 0);
  assert.equal(busy.incrementalTotalCents, 2000);
  assert.equal(busy.standaloneTotalCents, 2500);
});

test("admin time is excluded from both totals", () => {
  const result = estimate({
    messages: 100,
    dailyPeak: 10,
    hostingUsageUsd: 1,
    adminHours: 2,
    adminRateUsd: 40,
  });
  assert.equal(result.adminCents, 8000);
  assert.equal(result.standaloneTotalCents, 500);
});
