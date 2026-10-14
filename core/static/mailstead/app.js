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

  function init() {
    initMailNav();
    initThreadReply();
    initThreadMessages();
    initMessageFrames();
    initComposeModal();
    initComposeDraft();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
