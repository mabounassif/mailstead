/** Local review-queue records. Replace this module's fixtures when a real source exists. */

export type RequesterKind = "person" | "app" | "agent";

export type ReviewKind =
  | "document_access"
  | "outgoing_email"
  | "appointment"
  | "work_review"
  | "device_authorization"
  | "expired_permission";

export type DecisionAction =
  | "allow_24h"
  | "decline"
  | "approve_send"
  | "confirm_time"
  | "mark_reviewed"
  | "request_changes"
  | "allow_device"
  | "deny_device"
  | "dismiss_expired";

export type SnoozeChoice = "hour" | "evening" | "tomorrow";

export type Outcome = "approved" | "declined" | "changes_requested" | "dismissed";

export type DecisionReason =
  | "expired"
  | "invalid"
  | "missing_choice"
  | "missing_feedback"
  | "empty_message"
  | "busy";

export type MailAttachment = {
  id: string;
  name: string;
  sizeLabel: string;
  kindLabel: string;
  preview: string;
};

export type MailDraft = {
  toName: string;
  toAddress: string;
  subject: string;
  body: string;
  attachments: MailAttachment[];
};

export type ChoiceOption = {
  id: string;
  label: string;
  detail: string;
};

export type PlanColumn = {
  id: string;
  name: string;
  current: boolean;
  premium: string;
  deductible: string;
  rental: string;
  windshield: string;
  roadside: string;
  tradeoff: string;
};

export type ReviewSummary = {
  evidence: string;
  proposed: string;
  consequences: string;
};

export type DeviceInfo = {
  name: string;
  os: string;
  access: string;
  place: string;
};

export type Resolution = {
  action: DecisionAction;
  outcome: Outcome;
  label: string;
  detail: string;
  decidedAt: string;
};

export type ReviewItem = {
  id: string;
  kind: ReviewKind;
  requester: { name: string; kind: RequesterKind };
  typeLabel: string;
  requestedAt: string;
  expiresAt: string | null;
  timeSensitive: boolean;
  headline: string;
  explanation: string;
  folderName: string | null;
  disabledApprovalLabel: string | null;
  draft: MailDraft | null;
  options: ChoiceOption[];
  selectedOptionId: string | null;
  plans: PlanColumn[];
  recommendation: string;
  feedback: string;
  device: DeviceInfo | null;
  details: { id: string; title: string; body: string }[];
  summary: ReviewSummary;
  /** ISO time. A pending item stays out of the queue until this moment. */
  snoozeUntil: string | null;
  status: "pending" | "resolved";
  resolution?: Resolution;
};

export type DecisionResult =
  | { ok: true; item: ReviewItem; confirmation: string }
  | { ok: false; reason: DecisionReason; message: string };
