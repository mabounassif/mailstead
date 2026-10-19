(function () {
  var COMPOSE_DRAFT_KEY = "mailstead:compose-draft";
  var NAV_DESKTOP_KEY = "mailstead:nav-desktop-open";

  function initMailNav() {
    var btn = document.getElementById("mail-nav-toggle");
    var sidebar = document.getElementById("mail-sidebar");
    var backdrop = document.getElementById("mail-sidebar-backdrop");
    var shell = document.querySelector(".mail-shell");
    if (!btn || !sidebar || !shell) return;

    function isDesktop() {
      return window.matchMedia("(min-width: 1024px)").matches;
    }

    function readDesktopNavOpen() {
      try {
        var raw = localStorage.getItem(NAV_DESKTOP_KEY);
        if (raw === "0") return false;
        if (raw === "1") return true;
      } catch (err) {
        /* private mode / quota */
      }
      return true;
    }

    function writeDesktopNavOpen(open) {
      if (!isDesktop()) return;
      try {
        localStorage.setItem(NAV_DESKTOP_KEY, open ? "1" : "0");
      } catch (err) {
        /* ignore */
      }
    }

    function setOpen(open) {
      sidebar.classList.toggle("is-open", open);
      shell.classList.toggle("nav-closed", !open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (backdrop) {
        backdrop.hidden = !open;
        backdrop.classList.toggle("is-visible", open);
      }
      writeDesktopNavOpen(open);
    }

    function isOpen() {
      if (isDesktop()) {
        return !shell.classList.contains("nav-closed");
      }
      return sidebar.classList.contains("is-open");
    }

    btn.addEventListener("click", function () {
      setOpen(!isOpen());
    });

    if (backdrop) {
      backdrop.addEventListener("click", function () {
        setOpen(false);
      });
    }

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && isOpen() && !isDesktop()) {
        setOpen(false);
      }
    });

    if (isDesktop()) {
      setOpen(readDesktopNavOpen());
    } else {
      setOpen(false);
    }
  }

  function initThreadReply() {
    var root = document.getElementById("thread-reply");
    if (!root) return;

    var collapsed = document.getElementById("thread-reply-collapsed");
    var trigger = document.getElementById("thread-reply-trigger");
    var panel = document.getElementById("thread-reply-panel");
    var form = document.getElementById("thread-reply-form");
    var body = document.getElementById("thread-reply-body");
    var expand = document.getElementById("thread-reply-expand");
    var cancel = document.getElementById("thread-reply-cancel");
    var ccRow = document.getElementById("thread-reply-cc-row");
    var toValue = document.getElementById("thread-reply-to-value");

    var replyUrl = root.dataset.replyUrl;
    var replyAllUrl = root.dataset.replyAllUrl;
    var fullReply = root.dataset.fullReplyUrl;
    var fullReplyAll = root.dataset.fullReplyAllUrl;

    function setMode(mode) {
      var isAll = mode === "reply-all";
      if (form) form.action = isAll ? replyAllUrl : replyUrl;
      if (toValue) {
        toValue.textContent = isAll ? root.dataset.replyAllTo : root.dataset.replyTo;
      }
      if (ccRow) {
        var cc = (root.dataset.replyAllCc || "").trim();
        ccRow.hidden = !isAll || !cc;
      }
      if (expand) expand.href = isAll ? fullReplyAll : fullReply;
      root.querySelectorAll(".thread-reply__mode").forEach(function (btn) {
        var active = btn.dataset.mode === mode;
        btn.setAttribute("aria-pressed", active ? "true" : "false");
      });
    }

    function openPanel(mode) {
      if (mode) setMode(mode);
      if (collapsed) collapsed.hidden = true;
      if (panel) {
        panel.hidden = false;
      }
      root.classList.add("is-open");
      if (body) body.focus();
    }

    function closePanel() {
      if (collapsed) collapsed.hidden = false;
      if (panel) panel.hidden = true;
      root.classList.remove("is-open");
      if (body) body.value = "";
    }

    if (trigger) {
      trigger.addEventListener("click", function () {
        openPanel("reply");
      });
    }

    root.querySelectorAll("[data-open-reply]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        openPanel(btn.getAttribute("data-open-reply"));
      });
    });

    root.querySelectorAll(".thread-reply__mode").forEach(function (btn) {
      btn.addEventListener("click", function () {
        openPanel(btn.dataset.mode);
      });
    });

    if (cancel) {
      cancel.addEventListener("click", closePanel);
    }

    if (expand) {
      expand.addEventListener("click", function (e) {
        e.preventDefault();
        try {
          sessionStorage.setItem(COMPOSE_DRAFT_KEY, body ? body.value : "");
        } catch (err) {
          /* ignore quota / private mode */
        }
        window.location.href = expand.href;
      });
    }

    var initial = root.dataset.composeMode;
    if (initial === "reply-all") {
      openPanel("reply-all");
    } else if (initial === "reply") {
      openPanel("reply");
    } else {
      setMode("reply");
    }
  }

  function initComposeModal() {
    var overlay = document.getElementById("compose-overlay");
    if (!overlay) return;

    var backdrop = overlay.querySelector(".compose-overlay__backdrop");
    var closeHref = backdrop && backdrop.getAttribute("href");

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && closeHref) {
        e.preventDefault();
        window.location.href = closeHref;
      }
    });

    var to = document.getElementById("to");
    if (to) {
      to.focus();
    }
  }

  function resizeMessageFrame(frame) {
    try {
      var doc = frame.contentDocument;
      if (!doc || !doc.documentElement) return;
      var height = Math.max(
        doc.documentElement.scrollHeight,
        doc.body ? doc.body.scrollHeight : 0
      );
      if (height > 0) {
        frame.style.height = height + "px";
      }
    } catch (err) {
      /* sandbox or cross-origin */
    }
  }

  function bindMessageFrame(frame) {
    if (frame.dataset.frameBound === "1") return;
    frame.dataset.frameBound = "1";
    frame.addEventListener("load", function () {
      resizeMessageFrame(frame);
    });
    if (frame.contentDocument && frame.contentDocument.readyState === "complete") {
      resizeMessageFrame(frame);
    }
  }

  function ensureMessageFrameLoaded(frame) {
    var pending = frame.getAttribute("data-srcdoc");
    if (pending && !frame.getAttribute("srcdoc")) {
      frame.setAttribute("srcdoc", pending);
      frame.removeAttribute("data-srcdoc");
      bindMessageFrame(frame);
      return;
    }
    bindMessageFrame(frame);
    resizeMessageFrame(frame);
  }

  function initMessageFrames() {
    document.querySelectorAll(".message-frame").forEach(ensureMessageFrameLoaded);
  }

  function initThreadMessages() {
    document.querySelectorAll(".thread-message--collapsible").forEach(function (msg) {
      var toggle = msg.querySelector(".thread-message__toggle");
      var panel = msg.querySelector(".thread-message__expandable");
      if (!toggle || !panel) return;

      function setExpanded(expanded) {
        msg.classList.toggle("is-collapsed", !expanded);
        msg.classList.toggle("is-expanded", expanded);
        toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
        panel.hidden = !expanded;
        if (expanded) {
          panel.querySelectorAll(".message-frame").forEach(ensureMessageFrameLoaded);
        }
      }

      toggle.addEventListener("click", function () {
        if (msg.classList.contains("is-collapsed")) {
          setExpanded(true);
          return;
        }
        if (!msg.classList.contains("thread-message--last")) {
          setExpanded(false);
        }
      });
    });

    var anchor = document.querySelector(".thread-message--anchor.is-collapsed");
    if (anchor) {
      anchor.scrollIntoView({ block: "nearest" });
    }
  }

  function initComposeDraft() {
    var textarea = document.getElementById("body");
    if (!textarea || textarea.value) return;
    try {
      var draft = sessionStorage.getItem(COMPOSE_DRAFT_KEY);
      if (draft) {
        textarea.value = draft;
        sessionStorage.removeItem(COMPOSE_DRAFT_KEY);
      }
    } catch (err) {
      /* ignore */
    }
  }

  function initMembers() {
    document.querySelectorAll("[data-members]").forEach(function (root) {
      var toggle = root.querySelector(".members__toggle");
      var panel = root.querySelector(".members__panel");
      var search = root.querySelector(".members__search");
      var suggest = root.querySelector(".members__suggest");
      var pending = root.querySelector(".members__pending");
      var hidden = document.getElementById("chat-add-people");
      var known = ((document.getElementById("chat-compose-body") || {}).getAttribute && document.getElementById("chat-compose-body").getAttribute("data-known") || "").split(",").filter(Boolean);
      var staged = [];
      if (!toggle || !panel) return;

      function setOpen(open) {
        panel.hidden = !open;
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
        if (open && search) search.focus();
      }

      toggle.addEventListener("click", function () {
        setOpen(panel.hidden);
      });
      root.querySelectorAll("[data-members-close]").forEach(function (button) {
        button.addEventListener("click", function () {
          setOpen(false);
        });
      });
      document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !panel.hidden) setOpen(false);
      });

      function renderPending() {
        if (!pending || !hidden) return;
        hidden.value = staged.join(", ");
        pending.hidden = staged.length === 0;
        pending.innerHTML = "";
        staged.forEach(function (addr) {
          var row = document.createElement("li");
          row.className = "members__row";
          var face = document.createElement("span");
          face.className = "members__face";
          face.textContent = (addr[0] || "?").toUpperCase();
          var meta = document.createElement("span");
          meta.className = "members__meta";
          var name = document.createElement("span");
          name.className = "members__name";
          name.textContent = addr.split("@")[0];
          var note = document.createElement("span");
          note.className = "members__note";
          note.textContent = "Added when you send";
          meta.appendChild(name);
          meta.appendChild(note);
          var remove = document.createElement("button");
          remove.type = "button";
          remove.className = "members__remove";
          remove.setAttribute("aria-label", "Don't add " + addr);
          remove.textContent = "Remove";
          remove.addEventListener("click", function () {
            staged = staged.filter(function (item) { return item !== addr; });
            renderPending();
          });
          row.appendChild(face);
          row.appendChild(meta);
          row.appendChild(remove);
          pending.appendChild(row);
        });
      }

      function stage(addr) {
        addr = (addr || "").trim().toLowerCase();
        if (!addr || addr.indexOf("@") === -1 || staged.indexOf(addr) !== -1) return;
        staged.push(addr);
        renderPending();
        if (search) search.value = "";
        if (suggest) suggest.hidden = true;
      }

      var addBtn = root.querySelector(".members__add-btn");
      if (addBtn) addBtn.addEventListener("click", function () { stage(search && search.value); });
      if (search) {
        search.addEventListener("keydown", function (event) {
          if (event.key === "Enter") {
            event.preventDefault();
            stage(search.value);
          }
        });
        search.addEventListener("input", function () {
          if (!suggest) return;
          var query = search.value.trim().toLowerCase();
          suggest.innerHTML = "";
          if (!query) {
            suggest.hidden = true;
            return;
          }
          var hits = known.filter(function (addr) {
            return addr.toLowerCase().indexOf(query) !== -1 && staged.indexOf(addr.toLowerCase()) === -1;
          }).slice(0, 6);
          if (!hits.length) {
            suggest.hidden = true;
            return;
          }
          hits.forEach(function (addr) {
            var button = document.createElement("button");
            button.type = "button";
            button.textContent = addr;
            button.addEventListener("click", function () { stage(addr); });
            suggest.appendChild(button);
          });
          suggest.hidden = false;
        });
      }
    });
  }

  function initChatCompose() {
    document.querySelectorAll("form.chat-compose, form.new-chat, #chat-compose-form").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        var submitter = event.submitter;
        var dropping = submitter && submitter.name === "drop";
        if (dropping && !window.confirm("Remove this person? They get this message on BCC, then stay off later replies.")) {
          event.preventDefault();
          return;
        }
        var topic = form.querySelector("[name=subject]");
        if (topic && topic.required && !topic.value.trim()) {
          event.preventDefault();
          topic.focus();
          return;
        }
        var body = form.querySelector("[name=body]");
        if (!dropping && body && !body.value.trim()) {
          event.preventDefault();
          body.focus();
        }
      });
    });

    var box = document.getElementById("chat-compose-body");
    var hint = document.getElementById("mention-hint");
    if (!box || !hint) return;
    var known = (box.getAttribute("data-known") || "").split(",").filter(Boolean);
    box.addEventListener("input", function () {
      var match = box.value.match(/@([^\s@]*)$/);
      hint.innerHTML = "";
      if (!match) {
        hint.hidden = true;
        return;
      }
      var prefix = match[1].toLowerCase();
      var hits = known.filter(function (addr) {
        return addr.toLowerCase().indexOf(prefix) !== -1;
      }).slice(0, 5);
      if (!hits.length) {
        hint.hidden = true;
        return;
      }
      hits.forEach(function (addr) {
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = "@" + addr;
        button.addEventListener("click", function () {
          box.value = box.value.replace(/@([^\s@]*)$/, "@" + addr + " ");
          hint.hidden = true;
          box.focus();
        });
        hint.appendChild(button);
      });
      hint.hidden = false;
    });
  }

  function initSubjectFilter() {
    document.addEventListener("click", function (event) {
      document.querySelectorAll(".subject-filter[open]").forEach(function (menu) {
        if (!menu.contains(event.target)) menu.removeAttribute("open");
      });
    });
    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      document.querySelectorAll(".subject-filter[open]").forEach(function (menu) {
        menu.removeAttribute("open");
      });
    });
  }

  function initNewMessage() {
    document.querySelectorAll("[data-new-message]").forEach(function (form) {
      var input = form.querySelector(".slack-compose__to-input");
      var chips = form.querySelector(".slack-compose__chips");
      var suggest = form.querySelector(".slack-compose__suggest");
      var toField = form.querySelector("[name=to]");
      var channelField = form.querySelector("[name=channel]");
      var peopleOnly = form.hasAttribute("data-people-only");
      if (!input || !chips || !suggest || !toField) return;
      var targets = Array.prototype.map.call(form.querySelectorAll(".slack-compose__targets li"), function (item) {
        return { kind: item.getAttribute("data-kind"), id: item.getAttribute("data-id"), label: item.getAttribute("data-label") };
      });
      var chosen = [];
      var active = 0;

      function hasChannel() {
        return chosen.some(function (item) { return item.kind === "channel"; });
      }

      function hasPeople() {
        return chosen.some(function (item) { return item.kind !== "channel"; });
      }

      function alreadyChosen(id) {
        return chosen.some(function (item) { return item.id === id; });
      }

      function sync() {
        var channel = chosen.filter(function (item) { return item.kind === "channel"; })[0];
        var people = [];
        chosen.forEach(function (item) {
          if (item.kind !== "channel" && people.indexOf(item.id) === -1) people.push(item.id);
        });
        if (channelField) channelField.value = channel ? channel.id : "";
        toField.value = people.join(", ");
      }

      function renderChips() {
        chips.innerHTML = "";
        chosen.forEach(function (item, index) {
          var chip = document.createElement("li");
          chip.className = "slack-compose__chip";
          chip.textContent = (item.kind === "channel" ? "# " : "") + item.label;
          var remove = document.createElement("button");
          remove.type = "button";
          remove.setAttribute("aria-label", "Remove " + item.label);
          remove.textContent = "×";
          remove.addEventListener("click", function () {
            chosen.splice(index, 1);
            renderChips();
            input.focus();
          });
          chip.appendChild(remove);
          chips.appendChild(chip);
        });
        sync();
      }

      function matches() {
        if (hasChannel()) return [];
        var query = input.value.trim().toLowerCase().replace(/^[#@]/, "");
        return targets.filter(function (item) {
          if (peopleOnly && item.kind === "channel") return false;
          if (hasPeople() && item.kind === "channel") return false;
          if (alreadyChosen(item.id)) return false;
          return !query || item.label.toLowerCase().indexOf(query) !== -1 || item.id.toLowerCase().indexOf(query) !== -1;
        }).slice(0, 8);
      }

      function renderSuggest() {
        var items = matches();
        suggest.innerHTML = "";
        if (!items.length) {
          suggest.hidden = true;
          return;
        }
        if (active >= items.length) active = 0;
        items.forEach(function (item, index) {
          var row = document.createElement("li");
          row.setAttribute("role", "option");
          if (index === active) row.setAttribute("aria-selected", "true");
          var mark = document.createElement("span");
          mark.className = "slack-compose__mark";
          mark.textContent = item.kind === "channel" ? "#" : (item.label || "?").slice(0, 1).toUpperCase();
          var name = document.createElement("span");
          name.textContent = item.label;
          row.appendChild(mark);
          row.appendChild(name);
          row.addEventListener("mousedown", function (event) {
            event.preventDefault();
            pick(item);
          });
          suggest.appendChild(row);
        });
        suggest.hidden = false;
      }

      function pick(item) {
        chosen.push(item);
        input.value = "";
        active = 0;
        renderChips();
        renderSuggest();
      }

      input.addEventListener("focus", renderSuggest);
      input.addEventListener("input", function () { active = 0; renderSuggest(); });
      input.addEventListener("keydown", function (event) {
        var items = matches();
        if (event.key === "ArrowDown") {
          event.preventDefault();
          active = Math.min(active + 1, Math.max(items.length - 1, 0));
          renderSuggest();
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          active = Math.max(active - 1, 0);
          renderSuggest();
        } else if (event.key === "Enter" && !suggest.hidden && items[active]) {
          event.preventDefault();
          pick(items[active]);
        } else if ((event.key === "Enter" || event.key === ",") && input.value.indexOf("@") !== -1 && !hasChannel()) {
          event.preventDefault();
          input.value.split(",").forEach(function (part) {
            var addr = part.trim().toLowerCase();
            if (addr.indexOf("@") === -1 || alreadyChosen(addr)) return;
            chosen.push({ kind: "person", id: addr, label: addr });
          });
          input.value = "";
          renderChips();
          suggest.hidden = true;
        } else if (event.key === "Backspace" && !input.value && chosen.length) {
          chosen.pop();
          renderChips();
        } else if (event.key === "Escape") {
          suggest.hidden = true;
        } else if (event.key === "Enter") {
          event.preventDefault();
        }
      });
      document.addEventListener("click", function (event) {
        if (!form.contains(event.target)) suggest.hidden = true;
      });
      form.addEventListener("submit", sync);
    });
  }

  function init() {
    initMailNav();
    initThreadReply();
    initThreadMessages();
    initMessageFrames();
    initComposeModal();
    initComposeDraft();
    initSubjectFilter();
    initMembers();
    initChatCompose();
    initNewMessage();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
