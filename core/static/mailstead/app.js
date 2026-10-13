(function () {
  function initMailNav() {
    var btn = document.getElementById("mail-nav-toggle");
    var sidebar = document.getElementById("mail-sidebar");
    var backdrop = document.getElementById("mail-sidebar-backdrop");
    var shell = document.querySelector(".mail-shell");
    if (!btn || !sidebar || !shell) return;

    function isDesktop() {
      return window.matchMedia("(min-width: 1024px)").matches;
    }

    function setOpen(open) {
      sidebar.classList.toggle("is-open", open);
      shell.classList.toggle("nav-closed", !open);
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (backdrop) {
        backdrop.hidden = !open;
        backdrop.classList.toggle("is-visible", open);
      }
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
      setOpen(true);
    } else {
      setOpen(false);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initMailNav);
  } else {
    initMailNav();
  }
})();
