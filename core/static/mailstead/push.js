(function () {
  function csrfToken() {
    var match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function isStandalone() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  async function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return null;
    try {
      return await navigator.serviceWorker.register("/sw.js", { scope: "/" });
    } catch (e) {
      console.warn("service worker registration failed", e);
      return null;
    }
  }

  async function getPushManager() {
    if ("pushManager" in window) {
      return window.pushManager;
    }
    if (!("serviceWorker" in navigator)) return null;
    var reg = await navigator.serviceWorker.ready;
    return reg.pushManager;
  }

  function urlBase64ToUint8Array(base64String) {
    var padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    var base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    var raw = window.atob(base64);
    var output = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; ++i) {
      output[i] = raw.charCodeAt(i);
    }
    return output;
  }

  async function enablePush(publicKey, statusEl) {
    if (!publicKey) {
      if (statusEl) statusEl.textContent = "Push is not configured on the server.";
      return;
    }
    if (!("Notification" in window)) {
      if (statusEl) {
        statusEl.textContent =
          "Notifications are not available here. On iPhone, add Mailstead to your Home Screen and open it from the icon.";
      }
      return;
    }
    await registerServiceWorker();
    var permission = Notification.permission;
    if (permission === "default") {
      permission = await Notification.requestPermission();
    }
    if (permission !== "granted") {
      if (statusEl) statusEl.textContent = "Notification permission was denied.";
      return;
    }
    var pushManager = await getPushManager();
    if (!pushManager) {
      if (statusEl) statusEl.textContent = "Push is not supported in this browser.";
      return;
    }
    var subscription = await pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    });
    var json = subscription.toJSON();
    var resp = await fetch("/notifications/subscribe/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({
        endpoint: json.endpoint,
        keys: json.keys,
      }),
    });
    if (!resp.ok) {
      if (statusEl) statusEl.textContent = "Could not save subscription on the server.";
      return;
    }
    if (statusEl) statusEl.textContent = "This device is subscribed.";
    window.location.reload();
  }

  window.mailsteadPush = {
    enablePush: enablePush,
    isStandalone: isStandalone,
  };

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("push-enable-btn");
    if (!btn) return;
    var publicKey = btn.getAttribute("data-vapid-public");
    var statusEl = document.getElementById("push-status");
    if (!isStandalone() && /iPhone|iPad|iPod/.test(navigator.userAgent)) {
      if (statusEl) {
        statusEl.textContent =
          "On iPhone, use Safari Share → Add to Home Screen, then open Mailstead from the icon before enabling.";
      }
    }
    btn.addEventListener("click", function () {
      enablePush(publicKey, statusEl);
    });
  });
})();
