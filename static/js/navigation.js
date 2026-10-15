/* Native details and search links work without JS. Native dialogs add modal drawers. */
(() => {
  if (!window.HTMLDialogElement || !HTMLDialogElement.prototype.showModal)
    return;
  const menu = document.querySelector("[data-mobile-menu]");
  const panel = menu?.querySelector(".mobile-panel");
  const search = document.getElementById("search-dialog");
  const returnTargets = new WeakMap();

  function syncScrollLock() {
    document.documentElement.classList.toggle(
      "drawer-open",
      !!document.querySelector("dialog[open]"),
    );
  }
  function bindDialog(dialog, onClose = () => {}) {
    dialog.addEventListener("keydown", (event) => {
      if (event.key !== "Tab") return;
      const controls = [
        ...dialog.querySelectorAll(
          'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex="0"]',
        ),
      ].filter((el) => el.getClientRects().length);
      const first = controls[0];
      const last = controls.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    });
    dialog.querySelectorAll("[data-close-drawer]").forEach((button) => {
      button.hidden = false;
      button.addEventListener("click", () => dialog.close());
    });
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const bounds = dialog.getBoundingClientRect();
      if (
        event.clientX < bounds.left ||
        event.clientX > bounds.right ||
        event.clientY < bounds.top ||
        event.clientY > bounds.bottom
      )
        dialog.close();
    });
    dialog.addEventListener("close", () => {
      onClose();
      syncScrollLock();
      if (!document.querySelector("dialog[open]"))
        returnTargets.get(dialog)?.focus({ preventScroll: true });
    });
    dialog.addEventListener("click", (event) => {
      if (event.target.closest("a")) dialog.close();
    });
  }
  function openDialog(dialog, trigger) {
    for (const active of document.querySelectorAll("dialog[open]"))
      if (active !== dialog) active.close();
    returnTargets.set(dialog, trigger);
    if (!dialog.open) dialog.showModal();
    syncScrollLock();
  }

  if (menu && panel) {
    const trigger = menu.querySelector("summary");
    const dialog = document.createElement("dialog");
    dialog.id = "navigation-dialog";
    dialog.className = "drawer navigation-drawer";
    dialog.setAttribute("aria-label", "Navigation menu");
    panel.replaceWith(dialog);
    dialog.append(panel);
    trigger.setAttribute("aria-haspopup", "dialog");
    trigger.setAttribute("aria-controls", dialog.id);
    bindDialog(dialog, () => {
      menu.open = false;
    });
    menu.addEventListener("toggle", () => {
      if (menu.open) openDialog(dialog, trigger);
      else if (dialog.open) dialog.close();
    });
  }
  if (search) {
    bindDialog(search);
    document
      .querySelectorAll(".search-link, .mobile-secondary a[href*='?q=']")
      .forEach((trigger) => {
        trigger.setAttribute("aria-haspopup", "dialog");
        trigger.setAttribute("aria-controls", search.id);
        trigger.addEventListener("click", (event) => {
          if (
            event.button !== 0 ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey
          )
            return;
          event.preventDefault();
          openDialog(
            search,
            trigger.closest("dialog")
              ? document.querySelector(".search-link")
              : trigger,
          );
          search.querySelector("input").focus();
        });
      });
  }
})();
