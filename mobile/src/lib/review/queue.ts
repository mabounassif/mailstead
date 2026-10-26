import type {
  DecisionAction,
  DecisionResult,
  MailDraft,
  ReviewItem,
  ReviewKind,
  ReviewSummary,
  SnoozeChoice,
} from "./types";

/** Fraction of the slide track that counts as a completed gesture. */
export const SLIDE_COMMIT_AT = 0.92;

const KINDS = new Set<ReviewKind>([
  "document_access",
  "outgoing_email",
  "appointment",
  "work_review",
  "device_authorization",
  "expired_permission",
]);

const OPEN_ACTIONS: Record<ReviewKind, DecisionAction[]> = {
  document_access: ["allow_24h", "decline", "request_changes"],
  outgoing_email: ["approve_send", "request_changes"],
  appointment: ["confirm_time", "request_changes"],
  work_review: ["mark_reviewed", "request_changes"],
  device_authorization: ["allow_device", "deny_device"],
  expired_permission: ["dismiss_expired"],
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function iso(date: Date): string {
  return date.toISOString();
}

function shift(now: Date, ms: number): string {
  return iso(new Date(now.getTime() + ms));
}

function atLocal(now: Date, days: number, hour: number, minute: number): Date {
  const date = new Date(now.getTime());
  date.setDate(date.getDate() + days);
  date.setHours(hour, minute, 0, 0);
  return date;
}

function formatTime(date: Date): string {
  const hour24 = date.getHours();
  const hour = hour24 % 12 || 12;
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${hour}:${minute} ${hour24 >= 12 ? "PM" : "AM"}`;
}

export function formatDateTime(date: Date): string {
  return `${MONTHS[date.getMonth()]} ${date.getDate()}, ${date.getFullYear()}, ${formatTime(date)}`;
}

export function formatRequested(isoValue: string, now: Date): string {
  const date = new Date(isoValue);
  if (Number.isNaN(date.getTime())) return "";
  const delta = now.getTime() - date.getTime();
  const minutes = Math.round(delta / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return minutes === 1 ? "1 minute ago" : `${minutes} minutes ago`;
  const sameDay =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();
  if (sameDay) return formatTime(date);
  const yesterday = new Date(now.getTime());
  yesterday.setDate(now.getDate() - 1);
  const isYesterday =
    date.getFullYear() === yesterday.getFullYear() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getDate() === yesterday.getDate();
  if (isYesterday) return `Yesterday, ${formatTime(date)}`;
  return formatDateTime(date);
}

function appointmentLabel(date: Date, detail: string): { label: string; detail: string } {
  return {
    label: `${WEEKDAYS[date.getDay()]}, ${MONTHS[date.getMonth()]} ${date.getDate()} · ${formatTime(date)}`,
    detail,
  };
}

function summary(evidence: string, proposed: string, consequences: string): ReviewSummary {
  return { evidence, proposed, consequences };
}

export function createFixtures(now: Date): ReviewItem[] {
  const early = atLocal(now, 2, 8, 30);
  const midday = atLocal(now, 3, 13, 0);
  const dropoff = atLocal(now, 5, 7, 45);
  const earlyChoice = appointmentLabel(early, "Loaner car available");
  const middayChoice = appointmentLabel(midday, "Wait at the shop");
  const dropoffChoice = appointmentLabel(dropoff, "Early drop-off, keys in the box");

  return [
    {
      id: "tax-folder",
      kind: "document_access",
      requester: { name: "Tax Assistant", kind: "agent" },
      typeLabel: "Document access",
      requestedAt: shift(now, -26 * 60 * 1000),
      expiresAt: null,
      timeSensitive: false,
      headline: "Allow read access to your 2026 tax folder",
      explanation:
        "Tax Assistant prepared a draft-return request and needs to read the 2026 Taxes folder. Filing or sending anything needs a separate approval.",
      folderName: "2026 Taxes",
      disabledApprovalLabel: null,
      draft: null,
      options: [],
      selectedOptionId: null,
      plans: [],
      recommendation: "",
      feedback: "",
      device: null,
      details: [
        {
          id: "folder-contents",
          title: "What's in the folder",
          body: "Fictional demo files: a W-2 from Northwind Studio, a 1099-NEC from Harbor Civic, the property-tax bill, and charitable receipts. Access would be read-only.",
        },
      ],
      summary: summary(
        "The folder holds fictional 2026 tax documents. Tax Assistant has not opened them.",
        "Allow read-only access for 24 hours so it can prepare a draft return.",
        "Nothing is filed or sent. A later approval is still required before any return is submitted.",
      ),
      snoozeUntil: null,
      status: "pending",
    },
    {
      id: "accountant-reply",
      kind: "outgoing_email",
      requester: { name: "Nora Hale", kind: "person" },
      typeLabel: "Prepared message",
      requestedAt: shift(now, -26 * 60 * 60 * 1000),
      expiresAt: null,
      timeSensitive: false,
      headline: "Approve the reply to your accountant",
      explanation: "Nora Hale drafted a reply about the estimated tax payment. It stays here until you approve it.",
      folderName: null,
      disabledApprovalLabel: null,
      draft: {
        toName: "Priya Shah",
        toAddress: "priya.shah@northline-tax.example",
        subject: "Re: 2026 estimated tax payment",
        body: [
          "Hi Priya,",
          "",
          "Thanks for the reminder. I can send the third estimated payment of $2,400 by November 15. The mileage log and the Q3 worksheet are attached.",
          "",
          "I will be out the week of December 8, so the filing review is easier before then.",
          "",
          "Thank you,",
          "Maya Chen",
        ].join("\n"),
        attachments: [
          {
            id: "q3-pdf",
            name: "Q3-estimated-tax.pdf",
            sizeLabel: "186 KB",
            kindLabel: "PDF",
            preview:
              "Quarter 3 estimated tax worksheet for Maya Chen. Total due $2,400. Payment target November 15. This preview is sample text, not a real file.",
          },
          {
            id: "mileage-sheet",
            name: "Mileage-log-2026.xlsx",
            sizeLabel: "48 KB",
            kindLabel: "Spreadsheet",
            preview:
              "Sheet 1 lists 62 trips and 1,184 miles, mostly client visits between January and September. This preview is sample text, not a real file.",
          },
        ],
      },
      options: [],
      selectedOptionId: null,
      plans: [],
      recommendation: "",
      feedback: "",
      device: null,
      details: [
        {
          id: "draft-note",
          title: "What approval covers",
          body: "Approval records permission to send this reply and both attachments to Priya Shah. This demo does not transmit email.",
        },
      ],
      summary: summary(
        "Draft to Priya Shah with a fictional Q3 worksheet and mileage log attached.",
        "Approve sending that reply and both attachments.",
        "The decision is saved on this device. No email is sent.",
      ),
      snoozeUntil: null,
      status: "pending",
    },
    {
      id: "harbor-service",
      kind: "appointment",
      requester: { name: "Harbor Auto", kind: "agent" },
      typeLabel: "Question",
      requestedAt: shift(now, -8 * 60 * 1000),
      expiresAt: null,
      timeSensitive: true,
      headline: "Which service time should Harbor Auto hold?",
      explanation: "Harbor Auto found three openings and needs you to pick one. Holding a time does not approve a repair.",
      folderName: null,
      disabledApprovalLabel: null,
      draft: null,
      options: [
        { id: "early", ...earlyChoice },
        { id: "midday", ...middayChoice },
        { id: "dropoff", ...dropoffChoice },
      ],
      selectedOptionId: null,
      plans: [],
      recommendation: "",
      feedback: "",
      device: null,
      details: [
        {
          id: "hold",
          title: "How long the times are held",
          body: "These fictional openings are held until this evening. The shop does not charge anything for holding a time, and no repair is approved.",
        },
      ],
      summary: summary(
        "Three fictional service openings this week, including a loaner, a wait, and an early drop-off.",
        "Choose one time for Harbor Auto to hold.",
        "The shop holds that time only. No repair, part, or payment is approved.",
      ),
      snoozeUntil: null,
      status: "pending",
    },
    {
      id: "coverage-comparison",
      kind: "work_review",
      requester: { name: "Coverage Desk", kind: "agent" },
      typeLabel: "Finished work",
      requestedAt: shift(now, -3 * 60 * 60 * 1000),
      expiresAt: null,
      timeSensitive: false,
      headline: "Review your insurance options",
      explanation:
        "Coverage Desk finished a fictional comparison of your current auto policy and two alternatives. It needs you to look it over.",
      folderName: null,
      disabledApprovalLabel: null,
      draft: null,
      options: [],
      selectedOptionId: null,
      plans: [
        {
          id: "harbor",
          name: "Harbor Mutual",
          current: true,
          premium: "$1,428 a year",
          deductible: "$500",
          rental: "Included",
          windshield: "Full glass",
          roadside: "4 calls",
          tradeoff: "Current policy. Keeps rental coverage and full glass.",
        },
        {
          id: "northline-basic",
          name: "Northline Basic",
          current: false,
          premium: "$1,242 a year",
          deductible: "$1,000",
          rental: "Not included",
          windshield: "$200 limit",
          roadside: "None",
          tradeoff: "Saves $186 a year. Higher deductible, no rental or roadside.",
        },
        {
          id: "northline-plus",
          name: "Northline Plus",
          current: false,
          premium: "$1,510 a year",
          deductible: "$500",
          rental: "Included",
          windshield: "Full glass",
          roadside: "Unlimited",
          tradeoff: "Costs $82 more a year than current, with unlimited roadside.",
        },
      ],
      recommendation:
        "Harbor Mutual keeps the rental coverage and full glass from this fictional example. Northline Basic is $186 a year less, with a $1,000 deductible and no rental or roadside coverage.",
      feedback: "",
      device: null,
      details: [
        {
          id: "method",
          title: "How this comparison was made",
          body: "Fictional demo quotes for a 2019 Honda Civic garaged in Portland, Oregon. Premiums are invented for this sample and are not offers from an insurer.",
        },
      ],
      summary: summary(
        "Fictional quotes beside the current Harbor Mutual policy: premiums, deductibles, rental, glass, and roadside.",
        "Mark the comparison reviewed, or ask Coverage Desk to revise it.",
        "Reviewing does not purchase, renew, or change insurance. The Harbor Mutual policy stays as it is.",
      ),
      snoozeUntil: null,
      status: "pending",
    },
    {
      id: "pixel-tablet",
      kind: "device_authorization",
      requester: { name: "Pixel Tablet", kind: "app" },
      typeLabel: "New device",
      requestedAt: shift(now, -4 * 60 * 1000),
      expiresAt: shift(now, 45 * 60 * 1000),
      timeSensitive: true,
      headline: "Allow the Pixel Tablet to open your account?",
      explanation: "A sign-in from this tablet is waiting. Until you allow it, the tablet cannot open your mail.",
      folderName: null,
      disabledApprovalLabel: null,
      draft: null,
      options: [],
      selectedOptionId: null,
      plans: [],
      recommendation: "",
      feedback: "",
      device: {
        name: "Pixel Tablet",
        os: "Android 16",
        access: "Read and send mail, and see contacts, until you remove the device.",
        place: "Near Portland, Oregon",
      },
      details: [],
      summary: summary(
        "Fictional sign-in from a Pixel Tablet on Android 16, near Portland, Oregon. The request ends in about 45 minutes.",
        "Allow the tablet to read and send mail and see contacts until you remove it.",
        "This demo records the decision only. No device is actually authorized.",
      ),
      snoozeUntil: null,
      status: "pending",
    },
    {
      id: "invoices-expired",
      kind: "expired_permission",
      requester: { name: "Archive Helper", kind: "agent" },
      typeLabel: "Document access",
      requestedAt: shift(now, -5 * 24 * 60 * 60 * 1000),
      expiresAt: shift(now, -2 * 24 * 60 * 60 * 1000),
      timeSensitive: false,
      headline: "Access to last year's invoices has expired",
      explanation:
        'Archive Helper asked to read the "2025 Invoices" folder. The request ended before you decided, so allowing it now would not restore access.',
      folderName: "2025 Invoices",
      disabledApprovalLabel: "Allow for 7 days",
      draft: null,
      options: [],
      selectedOptionId: null,
      plans: [],
      recommendation: "",
      feedback: "",
      device: null,
      details: [],
      summary: summary(
        "Archive Helper asked to read the fictional 2025 Invoices folder for 7 days.",
        "Dismiss the request. Allowing it now would not restore access.",
        "Nothing is granted. The folder stays closed.",
      ),
      snoozeUntil: null,
      status: "pending",
    },
  ];
}

export function isItem(value: unknown): value is ReviewItem {
  if (!value || typeof value !== "object") return false;
  const item = value as ReviewItem;
  return typeof item.id === "string" && KINDS.has(item.kind) && (item.status === "pending" || item.status === "resolved");
}

export function isExpired(item: ReviewItem, now: Date): boolean {
  if (item.status === "resolved") return false;
  if (item.kind === "expired_permission") return true;
  if (!item.expiresAt) return false;
  const expiry = new Date(item.expiresAt).getTime();
  return !Number.isNaN(expiry) && expiry <= now.getTime();
}

export function isActionable(item: ReviewItem, now: Date): boolean {
  return item.status === "pending" && !isExpired(item, now) && !isSnoozed(item, now);
}

export function isSnoozed(item: ReviewItem, now: Date): boolean {
  if (item.status !== "pending" || !item.snoozeUntil) return false;
  const until = new Date(item.snoozeUntil).getTime();
  return !Number.isNaN(until) && until > now.getTime();
}

/** Requests still on the decision deck: pending, including expired, excluding snoozed. */
export function visiblePending(items: ReviewItem[], now: Date): ReviewItem[] {
  return items.filter((item) => item.status === "pending" && !isSnoozed(item, now));
}

export function pendingCount(items: ReviewItem[], now: Date): number {
  return visiblePending(items, now).length;
}

export function unresolvedItems(items: ReviewItem[]): ReviewItem[] {
  return items.filter((item) => item.status === "pending");
}

export function reviewedItems(items: ReviewItem[]): ReviewItem[] {
  return items
    .filter((item) => item.status === "resolved" && item.resolution)
    .slice()
    .sort((a, b) => (b.resolution?.decidedAt ?? "").localeCompare(a.resolution?.decidedAt ?? ""));
}

export function badgeLabel(count: number): string | null {
  if (count <= 0) return null;
  if (count > 99) return "99+";
  return String(count);
}

export function accessName(count: number): string {
  return `Review queue, ${count} pending`;
}

export function expirationCopy(item: ReviewItem, now: Date): string | null {
  if (!isExpired(item, now)) return null;
  if (item.expiresAt) {
    return `This request expired ${formatDateTime(new Date(item.expiresAt))}. Approval is turned off.`;
  }
  return "This request has expired. Approval is turned off.";
}

export function destinationAfterLater(
  pendingIds: string[],
  currentId: string,
): { type: "card"; id: string } | { type: "list" } {
  if (pendingIds.length <= 1) return { type: "list" };
  const index = pendingIds.indexOf(currentId);
  const next = pendingIds[(Math.max(index, 0) + 1) % pendingIds.length];
  if (!next || next === currentId) return { type: "list" };
  return { type: "card", id: next };
}

export function indexAfterResolve(ids: string[], resolvedId: string): number {
  const index = ids.indexOf(resolvedId);
  const remaining = ids.length - 1;
  if (remaining <= 0) return -1;
  if (index < 0) return 0;
  return Math.min(index, remaining - 1);
}

export function slideDecision(progress: number): "commit" | "reset" {
  return progress >= SLIDE_COMMIT_AT ? "commit" : "reset";
}

/** Horizontal browsing. The result is only a direction, never a decision. */
export function browseMove(dx: number, dy: number): -1 | 0 | 1 {
  if (Math.abs(dx) < 48 || Math.abs(dx) <= Math.abs(dy)) return 0;
  return dx < 0 ? 1 : -1;
}

export function browseTo(index: number, delta: -1 | 0 | 1, count: number): number {
  if (delta === 0 || count <= 0) return index;
  return Math.max(0, Math.min(count - 1, index + delta));
}

export function browsingEnabled(sliding: boolean): boolean {
  return !sliding;
}

export function deckLayout(viewport: number): { cardWidth: number; side: number; gap: number; pagerWidth: number } {
  const wide = viewport >= 840;
  if (wide) {
    const cardWidth = Math.min(640, Math.max(320, viewport - 32));
    return { cardWidth, side: 0, gap: 0, pagerWidth: cardWidth };
  }
  return { cardWidth: viewport, side: 0, gap: 0, pagerWidth: viewport };
}

export function statusLabel(item: ReviewItem, now: Date): string {
  if (isExpired(item, now)) return "Expired";
  if (item.kind === "document_access") return "Permission needed";
  if (item.kind === "outgoing_email") return "Approval needed";
  if (item.kind === "appointment") return "Needs an answer";
  if (item.kind === "work_review") return "Ready to review";
  if (item.kind === "device_authorization") return "Approval needed";
  return "Needs you";
}

export function primaryAction(item: ReviewItem, now: Date): DecisionAction {
  if (isExpired(item, now)) return "dismiss_expired";
  if (item.kind === "document_access") return "allow_24h";
  if (item.kind === "outgoing_email") return "approve_send";
  if (item.kind === "appointment") return "confirm_time";
  if (item.kind === "work_review") return "mark_reviewed";
  return "allow_device";
}

export function actionLabel(action: DecisionAction): string {
  if (action === "allow_24h") return "Allow for 24 hours";
  if (action === "decline") return "Decline";
  if (action === "approve_send") return "Approve and send";
  if (action === "confirm_time") return "Confirm time";
  if (action === "mark_reviewed") return "Mark reviewed";
  if (action === "request_changes") return "Request changes";
  if (action === "allow_device") return "Allow device";
  if (action === "deny_device") return "Deny";
  return "Dismiss";
}

export function busyLabel(action: DecisionAction): string {
  if (action === "allow_24h") return "Allowing…";
  if (action === "decline") return "Declining…";
  if (action === "approve_send") return "Approving…";
  if (action === "confirm_time") return "Confirming…";
  if (action === "mark_reviewed") return "Saving…";
  if (action === "request_changes") return "Saving note…";
  if (action === "allow_device") return "Allowing device…";
  if (action === "deny_device") return "Denying…";
  return "Dismissing…";
}

export function requiresConfirmation(action: DecisionAction): boolean {
  return action === "allow_24h" || action === "approve_send" || action === "allow_device";
}

export function isReversible(action: DecisionAction): boolean {
  return action !== "approve_send" && action !== "allow_device";
}

export function offersChanges(item: ReviewItem): boolean {
  return item.kind !== "device_authorization" && item.kind !== "expired_permission";
}

export function authorizationCopy(item: ReviewItem, now: Date): string {
  if (isExpired(item, now)) return "Dismissing removes this expired request. Access is not restored.";
  if (item.kind === "document_access") {
    return "Allowing records 24-hour read-only access. It does not file or send anything.";
  }
  if (item.kind === "outgoing_email") {
    return "Approving records permission to send this reply and its attachments. This demo does not send email.";
  }
  if (item.kind === "appointment") return "Confirming holds the selected time. It does not approve a repair.";
  if (item.kind === "work_review") {
    return "Marking reviewed records that you saw the comparison. It does not purchase or change insurance.";
  }
  return "Allowing records this device as trusted until you remove it. This demo does not authorize a real device.";
}

export function confirmationCopy(item: ReviewItem, action: DecisionAction): { title: string; body: string; confirm: string } {
  if (action === "allow_24h") {
    return {
      title: "Allow access for 24 hours?",
      body: `This records read-only access to “${item.folderName}” for 24 hours. Nothing is filed or sent. Submitting a return still needs a separate approval.`,
      confirm: "Allow for 24 hours",
    };
  }
  if (action === "approve_send" && item.draft) {
    const count = item.draft.attachments.length;
    const files = count === 1 ? "1 attachment" : `${count} attachments`;
    return {
      title: "Approve sending this reply?",
      body: `This records approval to send the reply to ${item.draft.toName} (${item.draft.toAddress}), including ${files}. This demo does not send email.`,
      confirm: "Approve and send",
    };
  }
  if (action === "allow_device" && item.device) {
    return {
      title: "Allow this device?",
      body: `This records ${item.device.name} (${item.device.os}) as allowed to read and send mail and see contacts until you remove it. This demo does not authorize a real device.`,
      confirm: "Allow device",
    };
  }
  return { title: "Confirm this decision?", body: authorizationCopy(item, new Date()), confirm: actionLabel(action) };
}

export function snoozeDeadline(choice: SnoozeChoice, now: Date): Date {
  if (choice === "hour") return new Date(now.getTime() + 60 * 60 * 1000);
  if (choice === "evening") {
    const evening = new Date(now.getTime());
    evening.setHours(19, 0, 0, 0);
    if (evening.getTime() <= now.getTime()) evening.setDate(evening.getDate() + 1);
    return evening;
  }
  const tomorrow = new Date(now.getTime());
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setHours(8, 0, 0, 0);
  return tomorrow;
}

export function snoozeNotice(choice: SnoozeChoice, now: Date): string {
  const deadline = snoozeDeadline(choice, now);
  if (choice === "tomorrow") return `Snoozed until tomorrow, ${formatTime(deadline)}.`;
  return `Snoozed until ${formatTime(deadline)}.`;
}

export function normalizeItem(item: ReviewItem): ReviewItem {
  return {
    ...item,
    snoozeUntil: item.snoozeUntil ?? null,
    summary: item.summary ?? {
      evidence: item.explanation,
      proposed: item.recommendation || item.typeLabel,
      consequences: "This demo records the decision on this device.",
    },
    plans: (item.plans ?? []).map((plan) => ({ ...plan, tradeoff: plan.tradeoff ?? "" })),
  };
}

function resolveCopy(item: ReviewItem, action: DecisionAction, now: Date): { label: string; detail: string; confirmation: string; outcome: ResolutionOutcome } {
  if (action === "allow_24h") {
    const end = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    const detail = `Read-only access to "${item.folderName}" until ${formatDateTime(end)}. Submitting anything still needs a separate approval.`;
    return {
      outcome: "approved",
      label: "Allowed for 24 hours",
      detail,
      confirmation: detail,
    };
  }
  if (action === "decline") {
    const detail = `${item.requester.name} cannot read "${item.folderName}".`;
    return { outcome: "declined", label: "Declined", detail, confirmation: detail };
  }
  if (action === "approve_send") {
    const draft = item.draft as MailDraft;
    const detail = `Approval recorded for ${draft.toName} (${draft.toAddress}). Subject: ${draft.subject}. No email was sent.`;
    return { outcome: "approved", label: "Approved to send", detail, confirmation: `Approval recorded for ${draft.toName}. No email was sent.` };
  }
  if (action === "confirm_time") {
    const option = item.options.find((entry) => entry.id === item.selectedOptionId);
    const detail = `Held ${option?.label}. ${option?.detail}. No repair was approved.`;
    return { outcome: "approved", label: "Time confirmed", detail, confirmation: `Time confirmed: ${option?.label}.` };
  }
  if (action === "mark_reviewed") {
    const detail = "Marked reviewed. No insurance was purchased or changed.";
    return {
      outcome: "approved",
      label: "Reviewed",
      detail,
      confirmation: "Marked reviewed. No insurance was purchased or changed.",
    };
  }
  if (action === "request_changes") {
    const detail = item.feedback.trim();
    return {
      outcome: "changes_requested",
      label: "Changes requested",
      detail,
      confirmation: `Note saved for ${item.requester.name}. Nothing was sent.`,
    };
  }
  if (action === "allow_device") {
    const device = item.device;
    const detail = `${device?.name} running ${device?.os} is recorded as allowed to read and send mail, and see contacts, until you remove the device. No device was authorized.`;
    return { outcome: "approved", label: "Device allowed", detail, confirmation: `${device?.name} recorded as allowed. No device was authorized.` };
  }
  if (action === "deny_device") {
    const detail = `${item.device?.name} was not given access.`;
    return { outcome: "declined", label: "Device denied", detail, confirmation: detail };
  }
  const when = item.expiresAt ? formatDateTime(new Date(item.expiresAt)) : "before you decided";
  const detail = `Nothing was granted. The request expired ${when}.`;
  return { outcome: "dismissed", label: "Dismissed", detail, confirmation: "Expired request dismissed." };
}

type ResolutionOutcome = "approved" | "declined" | "changes_requested" | "dismissed";

export function resolveItem(item: ReviewItem, action: DecisionAction, now: Date): DecisionResult {
  if (item.status !== "pending") {
    return { ok: false, reason: "invalid", message: "This request is already reviewed." };
  }
  const expired = isExpired(item, now);
  if (expired && action !== "dismiss_expired") {
    return { ok: false, reason: "expired", message: expirationCopy(item, now) ?? "This request expired. Approval is turned off." };
  }
  if (!expired && action === "dismiss_expired") {
    return { ok: false, reason: "invalid", message: "This request is still open." };
  }
  const allowed = expired ? ["dismiss_expired"] : OPEN_ACTIONS[item.kind];
  if (!allowed.includes(action)) {
    return { ok: false, reason: "invalid", message: "That response does not apply to this request." };
  }
  if (action === "confirm_time" && !item.options.some((option) => option.id === item.selectedOptionId)) {
    return { ok: false, reason: "missing_choice", message: "Choose a time first." };
  }
  if (action === "request_changes" && !item.feedback.trim()) {
    return { ok: false, reason: "missing_feedback", message: "Add a note before sending changes." };
  }
  if (action === "approve_send") {
    const draft = item.draft;
    if (!draft || !draft.toAddress.trim() || !draft.subject.trim() || !draft.body.trim()) {
      return { ok: false, reason: "empty_message", message: "Add a recipient, subject, and message before sending." };
    }
  }
  const copy = resolveCopy(item, action, now);
  return {
    ok: true,
    confirmation: copy.confirmation,
    item: {
      ...item,
      status: "resolved",
      resolution: {
        action,
        outcome: copy.outcome,
        label: copy.label,
        detail: copy.detail,
        decidedAt: now.toISOString(),
      },
    },
  };
}

export async function performDecision(
  item: ReviewItem,
  action: DecisionAction,
  options?: { delayMs?: number; clock?: () => Date },
): Promise<DecisionResult> {
  const clock = options?.clock ?? (() => new Date());
  const early = resolveItem(item, action, clock());
  if (!early.ok) return early;
  const delayMs = options?.delayMs ?? 0;
  if (delayMs > 0) {
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  return resolveItem(item, action, clock());
}

export class DecisionGate {
  private busy = false;

  tryBegin(): boolean {
    if (this.busy) return false;
    this.busy = true;
    return true;
  }

  end(): void {
    this.busy = false;
  }
}
