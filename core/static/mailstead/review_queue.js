(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.MailsteadReview = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  var SLIDE_COMMIT_AT = 0.92;
  var KINDS = {
    document_access: ["allow_24h", "decline", "request_changes"],
    outgoing_email: ["approve_send", "request_changes"],
    appointment: ["confirm_time", "request_changes"],
    work_review: ["mark_reviewed", "request_changes"],
    device_authorization: ["allow_device", "deny_device"],
    expired_permission: ["dismiss_expired"],
  };
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  function shift(now, ms) {
    return new Date(now.getTime() + ms).toISOString();
  }

  function atLocal(now, days, hour, minute) {
    var date = new Date(now.getTime());
    date.setDate(date.getDate() + days);
    date.setHours(hour, minute, 0, 0);
    return date;
  }

  function formatTime(date) {
    var hour24 = date.getHours();
    var hour = hour24 % 12 || 12;
    var minute = String(date.getMinutes()).padStart(2, "0");
    return hour + ":" + minute + " " + (hour24 >= 12 ? "PM" : "AM");
  }

  function formatDateTime(date) {
    return MONTHS[date.getMonth()] + " " + date.getDate() + ", " + date.getFullYear() + ", " + formatTime(date);
  }

  function formatRequested(isoValue, now) {
    var date = new Date(isoValue);
    if (Number.isNaN(date.getTime())) return "";
    var minutes = Math.round((now.getTime() - date.getTime()) / 60000);
    if (minutes < 1) return "Just now";
    if (minutes < 60) return minutes === 1 ? "1 minute ago" : minutes + " minutes ago";
    var sameDay = date.getFullYear() === now.getFullYear() && date.getMonth() === now.getMonth() && date.getDate() === now.getDate();
    if (sameDay) return formatTime(date);
    var yesterday = new Date(now.getTime());
    yesterday.setDate(now.getDate() - 1);
    var isYesterday =
      date.getFullYear() === yesterday.getFullYear() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getDate() === yesterday.getDate();
    if (isYesterday) return "Yesterday, " + formatTime(date);
    return formatDateTime(date);
  }

  function appointmentLabel(date, detail) {
    return {
      label: WEEKDAYS[date.getDay()] + ", " + MONTHS[date.getMonth()] + " " + date.getDate() + " · " + formatTime(date),
      detail: detail,
    };
  }

  function createFixtures(now) {
    var early = appointmentLabel(atLocal(now, 2, 8, 30), "Loaner car available");
    var midday = appointmentLabel(atLocal(now, 3, 13, 0), "Wait at the shop");
    var dropoff = appointmentLabel(atLocal(now, 5, 7, 45), "Early drop-off, keys in the box");
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
        explanation: "Tax Assistant prepared a draft-return request and needs to read the 2026 Taxes folder. Filing or sending anything needs a separate approval.",
        folderName: "2026 Taxes",
        disabledApprovalLabel: null,
        draft: null,
        options: [],
        selectedOptionId: null,
        plans: [],
        recommendation: "",
        feedback: "",
        device: null,
        details: [{ id: "folder-contents", title: "What's in the folder", body: "W-2 from Northwind Studio, 1099-NEC from Harbor Civic, the property-tax bill, and charitable receipts. Access is read-only." }],
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
          body: "Hi Priya,\n\nThanks for the reminder. I can send the third estimated payment of $2,400 by November 15. The mileage log and the Q3 worksheet are attached.\n\nI will be out the week of December 8, so the filing review is easier before then.\n\nThank you,\nMaya Chen",
          attachments: [
            { id: "q3-pdf", name: "Q3-estimated-tax.pdf", sizeLabel: "186 KB", kindLabel: "PDF", preview: "Quarter 3 estimated tax worksheet for Maya Chen. Total due $2,400. Payment target November 15. This preview is sample text, not a real file." },
            { id: "mileage-sheet", name: "Mileage-log-2026.xlsx", sizeLabel: "48 KB", kindLabel: "Spreadsheet", preview: "Sheet 1 lists 62 trips and 1,184 miles, mostly client visits between January and September. This preview is sample text, not a real file." },
          ],
        },
        options: [],
        selectedOptionId: null,
        plans: [],
        recommendation: "",
        feedback: "",
        device: null,
        details: [],
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
          Object.assign({ id: "early" }, early),
          Object.assign({ id: "midday" }, midday),
          Object.assign({ id: "dropoff" }, dropoff),
        ],
        selectedOptionId: null,
        plans: [],
        recommendation: "",
        feedback: "",
        device: null,
        details: [{ id: "hold", title: "How long the times are held", body: "These openings are held until this evening. The shop will not charge anything for holding a time." }],
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
        explanation: "Coverage Desk finished a fictional comparison of your current auto policy and two alternatives. It needs you to look it over.",
        folderName: null,
        disabledApprovalLabel: null,
        draft: null,
        options: [],
        selectedOptionId: null,
        plans: [
          { id: "harbor", name: "Harbor Mutual", current: true, premium: "$1,428 a year", deductible: "$500", rental: "Included", windshield: "Full glass", roadside: "4 calls", tradeoff: "Current policy. Keeps rental coverage and full glass." },
          { id: "northline-basic", name: "Northline Basic", current: false, premium: "$1,242 a year", deductible: "$1,000", rental: "Not included", windshield: "$200 limit", roadside: "None", tradeoff: "Saves $186 a year. Higher deductible, no rental or roadside." },
          { id: "northline-plus", name: "Northline Plus", current: false, premium: "$1,510 a year", deductible: "$500", rental: "Included", windshield: "Full glass", roadside: "Unlimited", tradeoff: "Costs $82 more a year than current, with unlimited roadside." },
        ],
        recommendation: "Harbor Mutual keeps the rental coverage and full glass from this fictional example. Northline Basic is $186 a year less, with a $1,000 deductible and no rental or roadside coverage.",
        feedback: "",
        device: null,
        details: [{ id: "method", title: "How this comparison was made", body: "Fictional demo quotes for a 2019 Honda Civic garaged in Portland, Oregon. Premiums are invented for this sample and are not offers from an insurer." }],
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
        device: { name: "Pixel Tablet", os: "Android 16", access: "Read and send mail, and see contacts, until you remove the device.", place: "Near Portland, Oregon" },
        details: [],
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
        explanation: 'Archive Helper asked to read the "2025 Invoices" folder. The request ended before you decided, so allowing it now would not restore access.',
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
        status: "pending",
      },
    ];
  }

  function isItem(value) {
    return Boolean(value && typeof value.id === "string" && KINDS[value.kind] && (value.status === "pending" || value.status === "resolved"));
  }

  function isExpired(item, now) {
    if (item.status === "resolved") return false;
    if (item.kind === "expired_permission") return true;
    if (!item.expiresAt) return false;
    var expiry = new Date(item.expiresAt).getTime();
    return !Number.isNaN(expiry) && expiry <= now.getTime();
  }

  function isSnoozed(item, now) {
    if (!item || item.status !== "pending" || !item.snoozeUntil) return false;
    var until = new Date(item.snoozeUntil).getTime();
    return !Number.isNaN(until) && until > now.getTime();
  }

  function isActionable(item, now) {
    return item.status === "pending" && !isExpired(item, now) && !isSnoozed(item, now);
  }

  function visiblePending(items, now) {
    return items.filter(function (item) { return item.status === "pending" && !isSnoozed(item, now); });
  }

  function pendingCount(items, now) {
    return visiblePending(items, now).length;
  }

  function unresolvedItems(items) {
    return items.filter(function (item) { return item.status === "pending"; });
  }

  function reviewedItems(items) {
    return items.filter(function (item) { return item.status === "resolved" && item.resolution; }).slice().sort(function (a, b) {
      return (b.resolution.decidedAt || "").localeCompare(a.resolution.decidedAt || "");
    });
  }

  function badgeLabel(count) {
    if (count <= 0) return null;
    if (count > 99) return "99+";
    return String(count);
  }

  function accessName(count) {
    return "Review queue, " + count + " pending";
  }

  function expirationCopy(item, now) {
    if (!isExpired(item, now)) return null;
    if (item.expiresAt) return "This request expired " + formatDateTime(new Date(item.expiresAt)) + ". Approval is turned off.";
    return "This request has expired. Approval is turned off.";
  }

  function destinationAfterLater(pendingIds, currentId) {
    if (pendingIds.length <= 1) return { type: "list" };
    var index = pendingIds.indexOf(currentId);
    var next = pendingIds[(Math.max(index, 0) + 1) % pendingIds.length];
    if (!next || next === currentId) return { type: "list" };
    return { type: "card", id: next };
  }

  function indexAfterResolve(ids, resolvedId) {
    var index = ids.indexOf(resolvedId);
    var remaining = ids.length - 1;
    if (remaining <= 0) return -1;
    if (index < 0) return 0;
    return Math.min(index, remaining - 1);
  }

  function slideDecision(progress) {
    return progress >= SLIDE_COMMIT_AT ? "commit" : "reset";
  }

  function browsingEnabled(sliding) {
    return !sliding;
  }

  var SUMMARIES = {
    "tax-folder": {
      evidence: "The folder holds fictional 2026 tax documents. Tax Assistant has not opened them.",
      proposed: "Allow read-only access for 24 hours so it can prepare a draft return.",
      consequences: "Nothing is filed or sent. A later approval is still required before any return is submitted.",
    },
    "accountant-reply": {
      evidence: "Draft to Priya Shah with a fictional Q3 worksheet and mileage log attached.",
      proposed: "Approve sending that reply and both attachments.",
      consequences: "The decision is saved on this device. No email is sent.",
    },
    "harbor-service": {
      evidence: "Three fictional service openings this week, including a loaner, a wait, and an early drop-off.",
      proposed: "Choose one time for Harbor Auto to hold.",
      consequences: "The shop holds that time only. No repair, part, or payment is approved.",
    },
    "coverage-comparison": {
      evidence: "Fictional quotes beside the current Harbor Mutual policy: premiums, deductibles, rental, glass, and roadside.",
      proposed: "Mark the comparison reviewed, or ask Coverage Desk to revise it.",
      consequences: "Reviewing does not purchase, renew, or change insurance. The Harbor Mutual policy stays as it is.",
    },
    "pixel-tablet": {
      evidence: "Fictional sign-in from a Pixel Tablet on Android 16, near Portland, Oregon.",
      proposed: "Allow the tablet to read and send mail and see contacts until you remove it.",
      consequences: "This demo records the decision only. No device is actually authorized.",
    },
    "invoices-expired": {
      evidence: "Archive Helper asked to read the fictional 2025 Invoices folder for 7 days.",
      proposed: "Dismiss the request. Allowing it now would not restore access.",
      consequences: "Nothing is granted. The folder stays closed.",
    },
  };

  function normalizeItem(item) {
    var known = SUMMARIES[item.id];
    var summary = item.summary || known || {
      evidence: item.explanation,
      proposed: item.recommendation || item.typeLabel,
      consequences: "This demo records the decision on this device.",
    };
    return Object.assign({}, item, {
      snoozeUntil: item.snoozeUntil || null,
      summary: summary,
      plans: (item.plans || []).map(function (plan) {
        return Object.assign({ tradeoff: "" }, plan);
      }),
    });
  }

  function statusLabel(item, now) {
    if (isExpired(item, now)) return "Expired";
    if (item.kind === "document_access") return "Permission needed";
    if (item.kind === "outgoing_email") return "Approval needed";
    if (item.kind === "appointment") return "Needs an answer";
    if (item.kind === "work_review") return "Ready to review";
    if (item.kind === "device_authorization") return "Approval needed";
    return "Needs you";
  }

  function primaryAction(item, now) {
    if (isExpired(item, now)) return "dismiss_expired";
    if (item.kind === "document_access") return "allow_24h";
    if (item.kind === "outgoing_email") return "approve_send";
    if (item.kind === "appointment") return "confirm_time";
    if (item.kind === "work_review") return "mark_reviewed";
    return "allow_device";
  }

  function actionLabel(action) {
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

  function busyLabel(action) {
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

  function requiresConfirmation(action) {
    return action === "allow_24h" || action === "approve_send" || action === "allow_device";
  }

  function isReversible(action) {
    return action !== "approve_send" && action !== "allow_device";
  }

  function offersChanges(item) {
    return item.kind !== "device_authorization" && item.kind !== "expired_permission";
  }

  function authorizationCopy(item, now) {
    if (isExpired(item, now)) return "Dismissing removes this expired request. Access is not restored.";
    if (item.kind === "document_access") return "Allowing records 24-hour read-only access. It does not file or send anything.";
    if (item.kind === "outgoing_email") return "Approving records permission to send this reply and its attachments. This demo does not send email.";
    if (item.kind === "appointment") return "Confirming holds the selected time. It does not approve a repair.";
    if (item.kind === "work_review") return "Marking reviewed records that you saw the comparison. It does not purchase or change insurance.";
    return "Allowing records this device as trusted until you remove it. This demo does not authorize a real device.";
  }

  function confirmationCopy(item, action) {
    if (action === "allow_24h") {
      return {
        title: "Allow access for 24 hours?",
        body: "This records read-only access to “" + item.folderName + "” for 24 hours. Nothing is filed or sent. Submitting a return still needs a separate approval.",
        confirm: "Allow for 24 hours",
      };
    }
    if (action === "approve_send" && item.draft) {
      var count = item.draft.attachments.length;
      var files = count === 1 ? "1 attachment" : count + " attachments";
      return {
        title: "Approve sending this reply?",
        body: "This records approval to send the reply to " + item.draft.toName + " (" + item.draft.toAddress + "), including " + files + ". This demo does not send email.",
        confirm: "Approve and send",
      };
    }
    if (action === "allow_device" && item.device) {
      return {
        title: "Allow this device?",
        body: "This records " + item.device.name + " (" + item.device.os + ") as allowed to read and send mail and see contacts until you remove it. This demo does not authorize a real device.",
        confirm: "Allow device",
      };
    }
    return { title: "Confirm this decision?", body: authorizationCopy(item, new Date()), confirm: actionLabel(action) };
  }

  function snoozeDeadline(choice, now) {
    if (choice === "hour") return new Date(now.getTime() + 60 * 60 * 1000);
    if (choice === "evening") {
      var evening = new Date(now.getTime());
      evening.setHours(19, 0, 0, 0);
      if (evening.getTime() <= now.getTime()) evening.setDate(evening.getDate() + 1);
      return evening;
    }
    var tomorrow = new Date(now.getTime());
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(8, 0, 0, 0);
    return tomorrow;
  }

  function snoozeNotice(choice, now) {
    var deadline = snoozeDeadline(choice, now);
    if (choice === "tomorrow") return "Snoozed until tomorrow, " + formatTime(deadline) + ".";
    return "Snoozed until " + formatTime(deadline) + ".";
  }

  function approvalLabel(item) {
    return actionLabel(primaryAction(item, new Date()));
  }

  function resolveItem(item, action, now) {
    if (item.status !== "pending") return { ok: false, reason: "invalid", message: "This request is already reviewed." };
    var expired = isExpired(item, now);
    if (expired && action !== "dismiss_expired") {
      return { ok: false, reason: "expired", message: expirationCopy(item, now) || "This request expired. Approval is turned off." };
    }
    if (!expired && action === "dismiss_expired") return { ok: false, reason: "invalid", message: "This request is still open." };
    var allowed = expired ? ["dismiss_expired"] : KINDS[item.kind];
    if (allowed.indexOf(action) === -1) return { ok: false, reason: "invalid", message: "That response does not apply to this request." };
    if (action === "confirm_time" && !item.options.some(function (option) { return option.id === item.selectedOptionId; })) {
      return { ok: false, reason: "missing_choice", message: "Choose a time first." };
    }
    if (action === "request_changes" && !String(item.feedback || "").trim()) {
      return { ok: false, reason: "missing_feedback", message: "Add a note before sending changes." };
    }
    if (action === "approve_send") {
      var draft = item.draft;
      if (!draft || !draft.toAddress.trim() || !draft.subject.trim() || !draft.body.trim()) {
        return { ok: false, reason: "empty_message", message: "Add a recipient, subject, and message before sending." };
      }
    }
    var copy = decisionCopy(item, action, now);
    var next = Object.assign({}, item, {
      status: "resolved",
      resolution: { action: action, outcome: copy.outcome, label: copy.label, detail: copy.detail, decidedAt: now.toISOString() },
    });
    return { ok: true, item: next, confirmation: copy.confirmation };
  }

  function decisionCopy(item, action, now) {
    if (action === "allow_24h") {
      var end = new Date(now.getTime() + 24 * 60 * 60 * 1000);
      var detail = 'Read-only access to "' + item.folderName + '" until ' + formatDateTime(end) + ". Submitting anything still needs a separate approval.";
      return { outcome: "approved", label: "Allowed for 24 hours", detail: detail, confirmation: detail };
    }
    if (action === "decline") {
      var declined = item.requester.name + ' cannot read "' + item.folderName + '".';
      return { outcome: "declined", label: "Declined", detail: declined, confirmation: declined };
    }
    if (action === "approve_send") {
      var sent = "Approval recorded for " + item.draft.toName + " (" + item.draft.toAddress + "). Subject: " + item.draft.subject + ". No email was sent.";
      return { outcome: "approved", label: "Approved to send", detail: sent, confirmation: "Approval recorded for " + item.draft.toName + ". No email was sent." };
    }
    if (action === "confirm_time") {
      var option = item.options.filter(function (entry) { return entry.id === item.selectedOptionId; })[0];
      var held = "Held " + option.label + ". " + option.detail + ". No repair was approved.";
      return { outcome: "approved", label: "Time confirmed", detail: held, confirmation: "Time confirmed: " + option.label + "." };
    }
    if (action === "mark_reviewed") {
      return {
        outcome: "approved",
        label: "Reviewed",
        detail: "Marked reviewed. No insurance was purchased or changed.",
        confirmation: "Marked reviewed. No insurance was purchased or changed.",
      };
    }
    if (action === "request_changes") {
      var note = String(item.feedback || "").trim();
      return { outcome: "changes_requested", label: "Changes requested", detail: note, confirmation: "Note saved for " + item.requester.name + ". Nothing was sent." };
    }
    if (action === "allow_device") {
      var device = item.device;
      var allowedDetail = device.name + " running " + device.os + " is recorded as allowed to read and send mail, and see contacts, until you remove the device. No device was authorized.";
      return { outcome: "approved", label: "Device allowed", detail: allowedDetail, confirmation: device.name + " recorded as allowed. No device was authorized." };
    }
    if (action === "deny_device") {
      var denied = item.device.name + " was not given access.";
      return { outcome: "declined", label: "Device denied", detail: denied, confirmation: denied };
    }
    var when = item.expiresAt ? formatDateTime(new Date(item.expiresAt)) : "before you decided";
    var dismissed = "Nothing was granted. The request expired " + when + ".";
    return { outcome: "dismissed", label: "Dismissed", detail: dismissed, confirmation: "Expired request dismissed." };
  }

  function storageKey() {
    var mailbox = "local";
    if (typeof document !== "undefined" && document.documentElement.dataset && document.documentElement.dataset.mailbox) {
      mailbox = document.documentElement.dataset.mailbox;
    }
    return "mailstead.reviewQueue.v1:" + mailbox;
  }

  function loadItems() {
    try {
      var raw = localStorage.getItem(storageKey());
      if (!raw) return { ok: true, items: null };
      var parsed = JSON.parse(raw);
      if (!parsed || parsed.version !== 1 || !Array.isArray(parsed.items) || !parsed.items.every(isItem)) return { ok: true, items: null };
      return { ok: true, items: parsed.items.map(normalizeItem) };
    } catch (err) {
      return { ok: false, message: "The review queue could not be loaded." };
    }
  }

  function readItems() {
    var loaded = loadItems();
    if (!loaded.ok) return null;
    return loaded.items;
  }

  function mountBadge() {
    if (typeof document === "undefined") return;
    var items = readItems() || createFixtures(new Date());
    var count = pendingCount(items, new Date());
    var label = badgeLabel(count);
    var name = accessName(count);
    document.querySelectorAll("[data-review-link]").forEach(function (link) {
      link.setAttribute("aria-label", name);
    });
    document.querySelectorAll("[data-review-badge]").forEach(function (badge) {
      if (!label) {
        badge.hidden = true;
        badge.textContent = "";
      } else {
        badge.hidden = false;
        badge.textContent = label;
      }
    });
  }

  return {
    createFixtures: function (now) { return createFixtures(now).map(normalizeItem); },
    isItem: isItem,
    isExpired: isExpired,
    isSnoozed: isSnoozed,
    isActionable: isActionable,
    visiblePending: visiblePending,
    pendingCount: pendingCount,
    unresolvedItems: unresolvedItems,
    reviewedItems: reviewedItems,
    badgeLabel: badgeLabel,
    accessName: accessName,
    expirationCopy: expirationCopy,
    destinationAfterLater: destinationAfterLater,
    indexAfterResolve: indexAfterResolve,
    slideDecision: slideDecision,
    browsingEnabled: browsingEnabled,
    resolveItem: resolveItem,
    formatDateTime: formatDateTime,
    formatRequested: formatRequested,
    approvalLabel: approvalLabel,
    statusLabel: statusLabel,
    primaryAction: primaryAction,
    actionLabel: actionLabel,
    busyLabel: busyLabel,
    requiresConfirmation: requiresConfirmation,
    isReversible: isReversible,
    offersChanges: offersChanges,
    authorizationCopy: authorizationCopy,
    confirmationCopy: confirmationCopy,
    snoozeDeadline: snoozeDeadline,
    snoozeNotice: snoozeNotice,
    normalizeItem: normalizeItem,
    storageKey: storageKey,
    readItems: readItems,
    loadItems: loadItems,
    mountBadge: mountBadge,
  };
});
