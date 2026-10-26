(function () {
  var Q = window.MailsteadReview;
  if (!Q) return;

  var state = {
    items: [],
    mode: "cards",
    index: 0,
    busy: false,
    busyAction: "",
    notice: "",
    error: "",
    loadError: "",
    open: {},
    changesOpen: false,
    snoozeOpen: false,
    confirm: "",
    undo: null,
    timer: 0,
  };
  var scrollLock = false;

  function nowDate() {
    return new Date();
  }

  function pending() {
    return Q.visiblePending(state.items, nowDate());
  }

  function current() {
    var items = pending();
    return items[state.index] || items[items.length - 1] || null;
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function button(label, className, attrs) {
    var node = el("button", className, label);
    node.type = "button";
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (value == null) return;
      if (key === "disabled") {
        node.disabled = Boolean(value);
        return;
      }
      node.setAttribute(key, value === true ? "true" : String(value));
    });
    return node;
  }

  function layoutIcon(kind) {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");
    function add(tag, attrs) {
      var node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      Object.keys(attrs).forEach(function (key) { node.setAttribute(key, attrs[key]); });
      svg.append(node);
    }
    if (kind === "list") {
      [["6", "8", "21"], ["12", "8", "21"], ["18", "8", "21"]].forEach(function (row) {
        add("line", { x1: row[1], x2: row[2], y1: row[0], y2: row[0] });
      });
      [["6", "3"], ["12", "3"], ["18", "3"]].forEach(function (dot) {
        add("line", { x1: dot[1], x2: dot[1], y1: dot[0], y2: dot[0] });
      });
    } else {
      add("rect", { x: "4", y: "4", width: "16", height: "16", rx: "2" });
      add("line", { x1: "4", x2: "20", y1: "9", y2: "9" });
    }
    return svg;
  }

  function layoutButton(kind, label, selected, action) {
    var node = document.createElement("button");
    node.type = "button";
    node.className = "review-view__btn" + (selected ? " is-selected" : "");
    node.setAttribute("data-action", action);
    node.setAttribute("aria-label", label);
    node.setAttribute("aria-pressed", selected ? "true" : "false");
    node.append(layoutIcon(kind));
    return node;
  }

  function announce(text) {
    var live = document.getElementById("review-live");
    if (!live || !text) return;
    live.textContent = "";
    window.setTimeout(function () {
      live.textContent = text;
    }, 30);
  }

  function persist() {
    if (state.loadError) return;
    try {
      localStorage.setItem(Q.storageKey(), JSON.stringify({ version: 1, items: state.items }));
    } catch (err) {
      /* storage can be unavailable */
    }
    Q.mountBadge();
  }

  function kindLabel(kind) {
    if (kind === "agent") return "Agent";
    if (kind === "app") return "App";
    return "Person";
  }

  function initials(name) {
    var parts = String(name || "").trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return "?";
    if (parts.length === 1) return parts[0].slice(0, 1).toUpperCase();
    return (parts[0].slice(0, 1) + parts[parts.length - 1].slice(0, 1)).toUpperCase();
  }

  function fact(label, value) {
    var row = el("div", "review-fact");
    row.append(el("div", "review-fact__label", label), el("div", "review-fact__value", value));
    return row;
  }

  function disclosure(id, label, body) {
    var wrap = el("div", "review-disclosure");
    var open = Boolean(state.open[id]);
    wrap.append(button(open ? "Hide " + label.toLowerCase() : label, "review-link", { "data-action": "toggle", "data-id": id, "aria-expanded": open ? "true" : "false" }));
    if (open) wrap.append(el("p", "review-copy", body));
    return wrap;
  }

  function buildSummary(item) {
    var box = el("div", "review-summary");
    var summary = item.summary || {};
    box.append(fact("Evidence", summary.evidence || ""), fact("Proposed action", summary.proposed || ""), fact("Consequences", summary.consequences || ""));
    return box;
  }

  function buildPlans(item) {
    var wrap = el("div", "review-plans");
    wrap.append(el("p", "review-fact__label", "Comparison"));
    if (item.recommendation) wrap.append(el("p", "review-copy", item.recommendation));
    item.plans.forEach(function (plan) {
      var card = el("div", "review-plan");
      var top = el("div", "review-plan__top");
      top.append(el("p", "review-plan__name", plan.name));
      if (plan.current) top.append(el("p", "review-plan__current", "Current"));
      card.append(top);
      card.append(el("p", "review-meta", plan.premium + " · " + plan.deductible + " deductible"));
      card.append(el("p", "review-meta", "Rental " + plan.rental + " · Glass " + plan.windshield + " · Roadside " + plan.roadside));
      if (plan.tradeoff) card.append(el("p", "review-plan__tradeoff", plan.tradeoff));
      wrap.append(card);
    });
    return wrap;
  }

  function buildEmail(item) {
    var draft = item.draft;
    var wrap = el("div", "review-block");
    wrap.append(fact("To", draft.toName + " · " + draft.toAddress), fact("Subject", draft.subject));
    var open = Boolean(state.open[item.id + ":message"]);
    var preview = !open && draft.body.length > 220 ? draft.body.slice(0, 220).trim() + "…" : draft.body;
    wrap.append(el("p", "review-copy review-pre", preview));
    if (draft.body.length > 220) {
      wrap.append(button(open ? "Show less" : "Read full message", "review-link", { "data-action": "toggle", "data-id": item.id + ":message" }));
    }
    draft.attachments.forEach(function (file) {
      var openFile = state.open[item.id + ":file"] === file.id;
      wrap.append(button(file.name + " · " + file.kindLabel + " · " + file.sizeLabel, "review-file", { "data-action": "file", "data-id": file.id, "aria-expanded": openFile ? "true" : "false" }));
      if (openFile) {
        var panel = el("div", "review-file-body");
        panel.append(el("p", "review-fact__label", file.name), el("p", "review-copy", file.preview));
        wrap.append(panel);
      }
    });
    return wrap;
  }

  function buildChoices(item) {
    var group = el("fieldset", "review-choices");
    group.append(el("legend", "review-fact__label", "Choose a time"));
    item.options.forEach(function (option) {
      var label = el("label", "review-choice" + (item.selectedOptionId === option.id ? " is-selected" : ""));
      var input = document.createElement("input");
      input.type = "radio";
      input.name = "time-" + item.id;
      input.value = option.id;
      input.checked = item.selectedOptionId === option.id;
      input.setAttribute("data-option", option.id);
      var text = el("span");
      text.append(el("span", "review-choice__label", option.label), el("span", "review-meta", option.detail));
      label.append(input, text);
      group.append(label);
    });
    return group;
  }

  function buildActions(item, active) {
    var now = nowDate();
    var expired = Q.isExpired(item, now);
    var busy = state.busy && active;
    var action = Q.primaryAction(item, now);
    var stack = el("div", "review-actions");
    stack.append(el("p", "review-authorize", Q.authorizationCopy(item, now)));
    if (active && state.changesOpen && Q.offersChanges(item)) {
      var label = el("label", "review-feedback");
      label.append(el("span", "review-fact__label", "What should change?"));
      var area = document.createElement("textarea");
      area.className = "review-input";
      area.value = item.feedback || "";
      area.setAttribute("data-feedback", "true");
      area.setAttribute("aria-label", "What should change?");
      label.append(area);
      stack.append(label);
      stack.append(button(state.busyAction === "request_changes" ? Q.busyLabel("request_changes") : "Send note", "review-primary", {
        "data-decision": "request_changes",
        disabled: busy || !String(item.feedback || "").trim(),
      }));
      stack.append(button("Cancel", "review-quiet", { "data-action": "close-changes", disabled: busy }));
      return stack;
    }
    var needsChoice = item.kind === "appointment" && !item.selectedOptionId;
    var primary = button(busy && state.busyAction === action ? Q.busyLabel(action) : Q.actionLabel(action), "review-primary", {
      "data-decision": action,
      "data-confirm": Q.requiresConfirmation(action) ? "true" : null,
      disabled: busy || needsChoice || !active,
    });
    if (needsChoice) primary.setAttribute("aria-describedby", "review-choice-hint");
    stack.append(primary);
    if (needsChoice) {
      var hint = el("p", "review-meta", "Choose a time first.");
      hint.id = "review-choice-hint";
      stack.append(hint);
    }
    if (!expired && Q.offersChanges(item)) {
      stack.append(button("Request changes", "review-secondary", { "data-action": "open-changes", disabled: busy || !active }));
    }
    var row = el("div", "review-tertiary");
    if (!expired) row.append(button("Later", "review-quiet", { "data-action": "later", disabled: busy || !active, "aria-expanded": active && state.snoozeOpen ? "true" : "false" }));
    if (item.kind === "document_access" && !expired) {
      row.append(button(busy && state.busyAction === "decline" ? Q.busyLabel("decline") : "Decline", "review-quiet review-quiet--danger", { "data-decision": "decline", disabled: busy || !active }));
    }
    if (item.kind === "device_authorization" && !expired) {
      row.append(button(busy && state.busyAction === "deny_device" ? Q.busyLabel("deny_device") : "Deny", "review-quiet review-quiet--danger", { "data-decision": "deny_device", disabled: busy || !active }));
    }
    if (item.kind === "outgoing_email") row.append(button("Edit message", "review-quiet", { "data-action": "edit", disabled: busy || !active }));
    stack.append(row);
    if (active && state.snoozeOpen) {
      var menu = el("div", "review-snooze");
      menu.setAttribute("role", "group");
      menu.setAttribute("aria-label", "Snooze");
      [["next", "Show next"], ["hour", "In 1 hour"], ["evening", "This evening"], ["tomorrow", "Tomorrow morning"]].forEach(function (choice) {
        menu.append(button(choice[1], "review-snooze__choice", { "data-snooze": choice[0] }));
      });
      menu.append(button("Cancel", "review-quiet", { "data-action": "close-snooze" }));
      stack.append(menu);
    }
    return stack;
  }

  function buildCard(item, active) {
    var now = nowDate();
    var expired = Q.isExpired(item, now);
    var card = el("article", "review-card" + (expired ? " is-expired" : "") + (state.busy && active ? " is-processing" : "") + (active ? "" : " is-peek"));
    if (active) card.setAttribute("aria-labelledby", "review-card-title");
    else card.setAttribute("aria-hidden", "true");
    if (state.busy && active) card.setAttribute("aria-busy", "true");
    if (!active) card.inert = true;
    var who = el("div", "review-who");
    var avatar = el("span", "review-avatar", initials(item.requester.name));
    avatar.setAttribute("aria-hidden", "true");
    var whoText = el("div", "review-who__text");
    whoText.append(el("p", "review-who__name", item.requester.name), el("p", "review-meta", kindLabel(item.requester.kind)));
    who.append(avatar, whoText, el("p", "review-time", Q.formatRequested(item.requestedAt, now)));
    var status = Q.statusLabel(item, now);
    if (item.timeSensitive && !expired) status += " · Time sensitive";
    var statusNode = el("p", "review-status" + (expired ? " is-expired" : ""), status);
    var title = el("h2", "review-card__title", item.headline);
    if (active) {
      title.id = "review-card-title";
      title.tabIndex = -1;
    }
    var body = el("div", "review-card__body");
    body.append(who, statusNode, title, el("p", "review-copy", item.explanation), buildSummary(item));
    var expiredText = Q.expirationCopy(item, now);
    if (expiredText) body.append(el("p", "review-expired-copy", expiredText));
    if (item.kind === "work_review") body.append(buildPlans(item));
    if (item.kind === "outgoing_email" && item.draft) body.append(buildEmail(item));
    if (item.kind === "appointment") body.append(buildChoices(item));
    item.details.forEach(function (detail) {
      body.append(disclosure(item.id + ":" + detail.id, detail.title, detail.body));
    });
    card.append(body, buildActions(item, active));
    return card;
  }

  function buildHeader(count) {
    var header = el("header", "review-head");
    header.setAttribute("data-pending-count", String(count));
    var heading = el("h1", "visually-hidden", "Needs you");
    heading.id = "review-page-title";
    header.append(heading);
    var row = el("div", "review-head__row");
    var tools = el("div", "review-view");
    tools.setAttribute("role", "group");
    tools.setAttribute("aria-label", "Layout");
    tools.append(
      layoutButton("card", "Show cards", state.mode === "cards", "mode-cards"),
      layoutButton("list", "Show list", state.mode === "list", "mode-list"),
    );
    var modes = el("div", "review-switch");
    modes.append(
      button("Pending", "review-switch__btn" + (state.mode !== "reviewed" ? " is-selected" : ""), { "data-action": "show-pending", "aria-pressed": state.mode !== "reviewed" }),
      button("Reviewed", "review-switch__btn" + (state.mode === "reviewed" ? " is-selected" : ""), { "data-action": "mode-reviewed", "aria-pressed": state.mode === "reviewed" }),
    );
    row.append(modes, tools);
    header.append(row);
    var items = pending();
    if (state.mode === "cards" && items.length) {
      var pager = el("div", "review-pager");
      pager.append(
        button("‹", "review-arrow", { "data-action": "prev", disabled: state.index <= 0 || state.busy, "aria-label": "Previous request" }),
        el("p", "review-position", Math.min(state.index, items.length - 1) + 1 + " of " + items.length),
        button("›", "review-arrow", { "data-action": "next", disabled: state.index >= items.length - 1 || state.busy, "aria-label": "Next request" }),
      );
      header.append(pager);
    }
    return header;
  }

  function snoozedHint() {
    var count = state.items.filter(function (item) { return Q.isSnoozed(item, nowDate()); }).length;
    if (count === 1) return "1 snoozed request will come back later.";
    if (count > 1) return count + " snoozed requests will come back later.";
    return "New requests will show up here.";
  }

  function buildPage() {
    var fragment = document.createDocumentFragment();
    var count = pending().length;
    fragment.append(buildHeader(count));
    if (state.notice) {
      var notice = el("div", "review-notice");
      notice.setAttribute("role", "status");
      notice.append(el("p", "", state.notice));
      var actions = el("div", "review-notice__actions");
      if (state.undo) actions.append(button("Undo", "review-link", { "data-action": "undo", disabled: state.busy }));
      actions.append(button("Dismiss", "review-link", { "data-action": "dismiss-notice" }));
      notice.append(actions);
      fragment.append(notice);
    }
    if (state.error) fragment.append(el("p", "review-error", state.error));
    var stage = el("div", "review-stage" + (state.mode === "cards" ? " review-stage--cards" : " is-scroll"));
    if (state.loadError) {
      var failed = el("div", "review-empty");
      failed.append(el("h2", "review-empty__title", "Couldn’t load requests"), el("p", "review-copy", state.loadError));
      failed.append(button("Try again", "review-primary", { "data-action": "retry" }));
      stage.append(failed);
      fragment.append(stage);
      return fragment;
    }
    var items = pending();
    if (state.mode === "cards" && items.length === 0) {
      var empty = el("div", "review-empty");
      var emptyTitle = el("h2", "review-empty__title", "You're all caught up.");
      emptyTitle.id = "review-empty-title";
      emptyTitle.tabIndex = -1;
      empty.append(emptyTitle, el("p", "review-meta", snoozedHint()));
      stage.append(empty);
    } else if (state.mode === "list") {
      var listTitle = el("h2", "visually-hidden", "Pending");
      listTitle.id = "review-card-title";
      listTitle.tabIndex = -1;
      stage.append(listTitle);
      if (!items.length) stage.append(el("p", "review-copy review-empty", snoozedHint()));
      items.forEach(function (item) {
        var row = button("", "review-row", { "data-action": "open-card", "data-id": item.id });
        row.append(el("span", "review-row__title", item.headline));
        row.append(el("span", "review-meta", item.requester.name + " · " + Q.statusLabel(item, nowDate()) + " · " + Q.formatRequested(item.requestedAt, nowDate())));
        stage.append(row);
      });
    } else if (state.mode === "reviewed") {
      stage.append(el("h2", "review-section", "Reviewed"));
      var reviewed = Q.reviewedItems(state.items);
      if (!reviewed.length) stage.append(el("p", "review-copy", "Nothing reviewed yet."));
      reviewed.forEach(function (item) {
        var card = el("article", "review-reviewed");
        card.append(el("p", "review-who__name", item.requester.name));
        card.append(el("p", "review-outcome review-outcome--" + (item.resolution.outcome || "dismissed"), item.resolution.label));
        card.append(el("p", "review-meta", Q.formatDateTime(new Date(item.resolution.decidedAt))), el("p", "review-copy", item.resolution.detail));
        stage.append(card);
      });
    } else {
      var deck = el("div", "review-deck");
      deck.id = "review-deck";
      items.forEach(function (item, index) {
        deck.append(buildCard(item, index === state.index));
      });
      stage.append(deck);
    }
    fragment.append(stage);
    return fragment;
  }

  function stepSize(deck) {
    var card = deck.querySelector(".review-card");
    if (!card) return 1;
    var styles = window.getComputedStyle(deck);
    var gap = parseFloat(styles.columnGap || styles.gap || "0") || 0;
    return card.getBoundingClientRect().width + gap;
  }

  function bindDeck(deck) {
    deck.addEventListener("scroll", function () {
      if (scrollLock || state.busy || state.changesOpen) return;
      var step = stepSize(deck);
      var next = Math.round(deck.scrollLeft / step);
      var max = deck.querySelectorAll(".review-card").length - 1;
      next = Math.max(0, Math.min(max, next));
      if (next === state.index) return;
      state.index = next;
      state.changesOpen = false;
      state.snoozeOpen = false;
      render({ keepScroll: true });
      announce(next + 1 + " of " + (max + 1));
    }, { passive: true });
  }

  function openConfirm(action) {
    var item = current();
    if (!item || state.busy) return;
    var copy = Q.confirmationCopy(item, action);
    state.confirm = action;
    document.getElementById("review-dialog-title").textContent = copy.title;
    document.getElementById("review-dialog-body").textContent = copy.body;
    document.getElementById("review-dialog-confirm").textContent = copy.confirm;
    document.getElementById("review-dialog").showModal();
    document.getElementById("review-dialog-confirm").focus();
  }

  function commit(action) {
    if (state.busy) return;
    var item = current();
    if (!item) return;
    var early = Q.resolveItem(item, action, nowDate());
    if (!early.ok) {
      state.error = early.message;
      render({ keepScroll: true });
      return;
    }
    state.busy = true;
    state.busyAction = action;
    state.error = "";
    state.notice = "";
    state.undo = null;
    var id = item.id;
    var before = pending().map(function (entry) { return entry.id; });
    var snapshot = Q.normalizeItem(item);
    render({ keepScroll: true });
    state.timer = window.setTimeout(function () {
      state.timer = 0;
      var latest = state.items.filter(function (entry) { return entry.id === id; })[0];
      var result = latest ? Q.resolveItem(latest, action, nowDate()) : { ok: false, message: "This request is no longer in the queue." };
      state.busy = false;
      state.busyAction = "";
      if (!result.ok) {
        state.error = result.message;
        render({ keepScroll: true });
        return;
      }
      state.items = state.items.map(function (entry) { return entry.id === id ? result.item : entry; });
      state.notice = result.confirmation;
      state.undo = Q.isReversible(action) ? snapshot : null;
      state.changesOpen = false;
      state.snoozeOpen = false;
      var nextIndex = Q.indexAfterResolve(before, id);
      state.index = nextIndex < 0 ? 0 : nextIndex;
      persist();
      render({ scrollToIndex: true, focus: true, announce: result.confirmation });
    }, 650);
  }

  function snooze(choice) {
    var item = current();
    if (!item || state.busy) return;
    state.snoozeOpen = false;
    if (choice === "next") {
      var ids = pending().map(function (entry) { return entry.id; });
      var dest = Q.destinationAfterLater(ids, item.id);
      if (dest.type === "list") {
        state.mode = "list";
        render({ focus: true });
        return;
      }
      var next = ids.indexOf(dest.id);
      if (next >= 0) state.index = next;
      render({ scrollToIndex: true, focus: true });
      return;
    }
    var before = pending().map(function (entry) { return entry.id; });
    var clock = nowDate();
    state.undo = Q.normalizeItem(item);
    state.items = state.items.map(function (entry) {
      return entry.id === item.id ? Object.assign({}, entry, { snoozeUntil: Q.snoozeDeadline(choice, clock).toISOString() }) : entry;
    });
    state.notice = Q.snoozeNotice(choice, clock);
    var nextIndex = Q.indexAfterResolve(before, item.id);
    state.index = nextIndex < 0 ? 0 : nextIndex;
    persist();
    render({ scrollToIndex: true, focus: true, announce: state.notice });
  }

  function undo() {
    if (!state.undo || state.busy) return;
    var snapshot = state.undo;
    state.undo = null;
    state.items = state.items.map(function (entry) { return entry.id === snapshot.id ? snapshot : entry; });
    var index = pending().findIndex(function (entry) { return entry.id === snapshot.id; });
    if (index >= 0) state.index = index;
    state.mode = "cards";
    state.notice = "Restored to pending.";
    persist();
    render({ scrollToIndex: true, focus: true, announce: state.notice });
  }

  function retry() {
    var loaded = Q.loadItems();
    if (!loaded.ok) {
      state.loadError = loaded.message;
      render();
      return;
    }
    state.loadError = "";
    state.items = loaded.items ? loaded.items.map(Q.normalizeItem) : Q.createFixtures(nowDate());
    state.index = 0;
    persist();
    render({ scrollToIndex: true });
  }

  function onClick(event) {
    var node = event.target.closest("[data-action], [data-decision], [data-snooze]");
    if (!node || node.disabled) return;
    var action = node.getAttribute("data-action");
    var decision = node.getAttribute("data-decision");
    var snoozeChoice = node.getAttribute("data-snooze");
    if (decision) {
      event.preventDefault();
      if (node.getAttribute("data-confirm") === "true") openConfirm(decision);
      else commit(decision);
      return;
    }
    if (snoozeChoice) {
      snooze(snoozeChoice);
      return;
    }
    if (action === "prev" || action === "next") {
      var items = pending();
      state.index = action === "next" ? Math.min(items.length - 1, state.index + 1) : Math.max(0, state.index - 1);
      state.changesOpen = false;
      state.snoozeOpen = false;
      render({ scrollToIndex: true });
      announce(state.index + 1 + " of " + items.length);
    } else if (action === "later") {
      state.changesOpen = false;
      state.snoozeOpen = !state.snoozeOpen;
      render({ keepScroll: true });
    } else if (action === "close-snooze") {
      state.snoozeOpen = false;
      render({ keepScroll: true });
    } else if (action === "show-pending") {
      if (state.mode === "reviewed") state.mode = "cards";
      state.changesOpen = false;
      render({ scrollToIndex: true });
    } else if (action === "mode-cards" || action === "mode-list" || action === "mode-reviewed") {
      state.mode = action === "mode-list" ? "list" : action === "mode-reviewed" ? "reviewed" : "cards";
      state.changesOpen = false;
      state.snoozeOpen = false;
      render({ scrollToIndex: true });
    } else if (action === "toggle") {
      var id = node.getAttribute("data-id");
      state.open[id] = !state.open[id];
      render({ keepScroll: true });
    } else if (action === "file") {
      var fileId = node.getAttribute("data-id");
      var item = current();
      if (!item) return;
      var key = item.id + ":file";
      state.open[key] = state.open[key] === fileId ? "" : fileId;
      render({ keepScroll: true });
    } else if (action === "open-changes") {
      state.snoozeOpen = false;
      state.changesOpen = true;
      render({ keepScroll: true });
      var area = document.querySelector("[data-feedback]");
      if (area) {
        area.focus();
        window.setTimeout(function () {
          var send = document.querySelector("[data-decision='request_changes']");
          (send || area).scrollIntoView({ block: "nearest" });
        }, 280);
      }
    } else if (action === "close-changes") {
      state.changesOpen = false;
      render({ keepScroll: true });
    } else if (action === "edit") {
      state.mode = "edit";
      render();
    } else if (action === "open-card") {
      var target = node.getAttribute("data-id");
      var index = pending().findIndex(function (entry) { return entry.id === target; });
      state.index = Math.max(0, index);
      state.mode = "cards";
      render({ scrollToIndex: true });
    } else if (action === "dismiss-notice") {
      state.notice = "";
      state.undo = null;
      render({ keepScroll: true });
    } else if (action === "undo") {
      undo();
    } else if (action === "retry") {
      retry();
    } else if (action === "edit-done") {
      state.mode = "cards";
      render({ scrollToIndex: true, focus: true });
    }
  }

  function renderEdit() {
    var item = state.items.filter(function (entry) { return entry.kind === "outgoing_email" && entry.draft; })[0];
    var root = document.getElementById("review-root");
    if (!item) {
      state.mode = "cards";
      renderQueue();
      return;
    }
    var page = document.createDocumentFragment();
    page.append(buildHeader(pending().length));
    var form = el("form", "review-editor");
    form.addEventListener("submit", function (event) { event.preventDefault(); });
    form.append(el("p", "review-meta", "Edits stay on this device. Approving still happens from the review card, and this demo does not send email."));
    [["toName", "Name"], ["toAddress", "Email"], ["subject", "Subject"]].forEach(function (pair) {
      var label = el("label", "review-field");
      label.append(el("span", "review-fact__label", pair[1]));
      var input = document.createElement("input");
      input.className = "review-input";
      input.value = item.draft[pair[0]];
      input.setAttribute("data-draft", pair[0]);
      if (pair[0] === "toAddress") input.autocomplete = "off";
      label.append(input);
      form.append(label);
    });
    var message = el("label", "review-field");
    message.append(el("span", "review-fact__label", "Message"));
    var area = document.createElement("textarea");
    area.className = "review-input review-input--message";
    area.value = item.draft.body;
    area.setAttribute("data-draft", "body");
    message.append(area);
    form.append(message);
    item.draft.attachments.forEach(function (file) {
      var block = el("div", "review-file-body");
      block.append(el("p", "review-choice__label", file.name), el("p", "review-meta", file.kindLabel + " · " + file.sizeLabel), el("p", "review-copy", file.preview));
      form.append(block);
    });
    form.append(button("Back to review", "review-primary", { "data-action": "edit-done" }));
    page.append(form);
    root.replaceChildren(page);
  }

  function render(options) {
    if (state.mode === "edit") renderEdit();
    else renderQueue(options || {});
  }

  function renderQueue(options) {
    var root = document.getElementById("review-root");
    var items = pending();
    if (state.index > items.length - 1) state.index = Math.max(0, items.length - 1);
    var previous = document.getElementById("review-deck");
    var previousLeft = previous ? previous.scrollLeft : 0;
    root.replaceChildren(buildPage());
    var deck = document.getElementById("review-deck");
    if (deck) {
      bindDeck(deck);
      window.requestAnimationFrame(function () {
        if (!deck.isConnected) return;
        scrollLock = true;
        deck.scrollLeft = options.scrollToIndex ? state.index * stepSize(deck) : previousLeft;
        window.requestAnimationFrame(function () {
          scrollLock = false;
        });
      });
    }
    if (options.focus) {
      var title = document.getElementById("review-card-title") || document.getElementById("review-empty-title");
      if (title) title.focus();
    }
    if (options.announce) announce(options.announce);
    Q.mountBadge();
  }

  function init() {
    var app = document.getElementById("review-app");
    if (!app) return;
    var loaded = Q.loadItems();
    if (!loaded.ok) {
      state.loadError = loaded.message;
      state.items = [];
    } else {
      state.items = loaded.items ? loaded.items.map(Q.normalizeItem) : Q.createFixtures(nowDate());
      persist();
    }
    app.addEventListener("click", onClick);
    app.addEventListener("change", function (event) {
      var input = event.target.closest("[data-option]");
      if (!input) return;
      var item = current();
      if (!item) return;
      state.items = state.items.map(function (entry) {
        return entry.id === item.id ? Object.assign({}, entry, { selectedOptionId: input.value }) : entry;
      });
      persist();
      render({ keepScroll: true });
    });
    app.addEventListener("input", function (event) {
      var feedback = event.target.closest("[data-feedback]");
      var draftField = event.target.closest("[data-draft]");
      if (feedback) {
        var item = current();
        if (!item) return;
        item.feedback = feedback.value;
        persist();
        var send = document.querySelector("[data-decision='request_changes']");
        if (send) send.disabled = !feedback.value.trim() || state.busy;
        return;
      }
      if (draftField) {
        var email = state.items.filter(function (entry) { return entry.kind === "outgoing_email" && entry.draft; })[0];
        if (!email) return;
        var draft = Object.assign({}, email.draft);
        draft[draftField.getAttribute("data-draft")] = draftField.value;
        email.draft = draft;
        persist();
      }
    });
    document.getElementById("review-dialog-cancel").addEventListener("click", function () {
      state.confirm = "";
      document.getElementById("review-dialog").close();
    });
    document.getElementById("review-dialog-confirm").addEventListener("click", function () {
      var action = state.confirm;
      state.confirm = "";
      document.getElementById("review-dialog").close();
      if (action) commit(action);
    });
    document.addEventListener("keydown", function (event) {
      if (state.mode !== "cards" || state.busy || state.confirm) return;
      var tag = event.target && event.target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || (event.target && event.target.isContentEditable)) return;
      if (event.key === "ArrowRight") {
        event.preventDefault();
        state.index = Math.min(pending().length - 1, state.index + 1);
        state.changesOpen = false;
        state.snoozeOpen = false;
        render({ scrollToIndex: true });
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        state.index = Math.max(0, state.index - 1);
        state.changesOpen = false;
        state.snoozeOpen = false;
        render({ scrollToIndex: true });
      }
    });
    window.setInterval(function () {
      if (state.mode !== "cards" || state.busy || state.loadError) return;
      var count = pending().length;
      var node = document.querySelector("[data-pending-count]");
      var shown = node ? Number(node.getAttribute("data-pending-count")) : count;
      var item = current();
      var expired = item ? Q.isExpired(item, nowDate()) : false;
      var card = document.querySelectorAll(".review-card")[state.index];
      var shownExpired = card && card.classList.contains("is-expired");
      if (shown !== count || Boolean(shownExpired) !== expired) render({ keepScroll: true });
    }, 5000);
    render({ scrollToIndex: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
