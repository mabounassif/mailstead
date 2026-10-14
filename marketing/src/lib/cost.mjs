import { railway, resend } from "../data/pricing.mjs";

export function usd(cents) {
  return cents / 100;
}

export function formatUsd(cents) {
  const sign = cents < 0 ? "-" : "";
  const abs = Math.abs(cents);
  return `${sign}$${(abs / 100).toFixed(2)}`;
}

/** Railway bill for a plan: subscription plus usage above the included credit. */
export function hostingCents(usageUsd, plan) {
  const fee = Math.round(plan.monthlyFeeUsd * 100);
  const included = Math.round(plan.includedUsageUsd * 100);
  const usage = Math.round(Number(usageUsd) * 100);
  return fee + Math.max(0, usage - included);
}

/**
 * Extra hosting dollars if the workspace subscription is already paid.
 * `unusedCreditUsd` is remaining included usage, not the plan fee.
 */
export function incrementalHostingCents(usageUsd, unusedCreditUsd) {
  const usage = Math.round(Number(usageUsd) * 100);
  const unused = Math.round(Number(unusedCreditUsd) * 100);
  return Math.max(0, usage - unused);
}

export function overageCents(messages, plan) {
  if (messages <= plan.includedEmails) return 0;
  if (plan.overagePerThousandUsd == null) return null;
  const extra = messages - plan.includedEmails;
  const buckets = Math.ceil(extra / 1000);
  return Math.round(buckets * plan.overagePerThousandUsd * 100);
}

export function planFitsDaily(plan, dailyPeak) {
  if (plan.dailyLimit == null) return true;
  if (dailyPeak == null || dailyPeak === "") return true;
  return Number(dailyPeak) <= plan.dailyLimit;
}

/**
 * Smallest included-quota plan that covers monthly volume and the daily peak.
 * Overage is reported but not used to pick a cheaper plan.
 */
export function selectResend(messages, dailyPeak) {
  const volume = Math.max(0, Math.floor(Number(messages) || 0));
  const eligible = resend.plans.filter((plan) => planFitsDaily(plan, dailyPeak));
  const covering = eligible
    .filter((plan) => volume <= plan.includedEmails)
    .sort((a, b) => a.monthlyFeeUsd - b.monthlyFeeUsd || a.includedEmails - b.includedEmails);
  if (covering.length) {
    const plan = covering[0];
    const free = resend.plans.find((item) => item.id === "free");
    const freeExcluded =
      free != null &&
      volume <= free.includedEmails &&
      !planFitsDaily(free, dailyPeak) &&
      plan.id !== "free";
    return {
      ok: true,
      plan,
      feeCents: Math.round(plan.monthlyFeeUsd * 100),
      overageCents: 0,
      reason: freeExcluded ? "daily-limit" : null,
    };
  }
  const freeBlocked = resend.plans.find((plan) => plan.id === "free" && volume <= plan.includedEmails);
  return {
    ok: false,
    plan: null,
    feeCents: null,
    overageCents: null,
    reason: freeBlocked && !planFitsDaily(freeBlocked, dailyPeak)
      ? "daily-limit"
      : "above-listed-plans",
  };
}

export function estimate(input) {
  const mailboxes = Math.max(0, Math.floor(Number(input.mailboxes) || 0));
  const messages = Math.max(0, Math.floor(Number(input.messages) || 0));
  const dailyPeak = input.dailyPeak === "" || input.dailyPeak == null ? null : Math.max(0, Math.floor(Number(input.dailyPeak)));
  const usageUsd = Math.max(0, Number(input.hostingUsageUsd) || 0);
  const plan = railway.plans[input.hostingPlan] || railway.plans.hobby;
  const domainAnnual = Math.max(0, Number(input.domainAnnualUsd) || 0);
  const backups = Math.max(0, Number(input.backupsMonthlyUsd) || 0);
  const adminHours = Math.max(0, Number(input.adminHours) || 0);
  const adminRate = Math.max(0, Number(input.adminRateUsd) || 0);
  const unusedCredit = Math.max(0, Number(input.unusedCreditUsd) || 0);
  const alreadyHosting = Boolean(input.alreadyHosting);

  const provider = selectResend(messages, dailyPeak);
  const domainCents = Math.round((domainAnnual / 12) * 100);
  const backupCents = Math.round(backups * 100);
  const adminCents = Math.round(adminHours * adminRate * 100);
  const standaloneHosting = hostingCents(usageUsd, plan);
  const incrementalHosting = alreadyHosting ? incrementalHostingCents(usageUsd, unusedCredit) : standaloneHosting;

  const providerCents = provider.ok ? provider.feeCents : null;
  const addons = domainCents + backupCents;

  return {
    mailboxes,
    messages,
    dailyPeak,
    hostingPlan: plan,
    provider,
    domainCents,
    backupCents,
    adminCents,
    standaloneHostingCents: standaloneHosting,
    incrementalHostingCents: incrementalHosting,
    standaloneTotalCents: providerCents == null ? null : standaloneHosting + providerCents + addons,
    incrementalTotalCents: providerCents == null ? null : incrementalHosting + providerCents + addons,
    currency: "USD",
  };
}
