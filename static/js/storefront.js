/* Small progressive enhancements; all destinations and forms remain server rendered. */
(() => {
  document.querySelectorAll("[data-card-preview]").forEach((button) => {
    const card = button.closest(".product-card");
    const initialLabel = button.getAttribute("aria-label");
    button.hidden = false;
    button.addEventListener("click", () => {
      const alternate = card.classList.toggle("alternate-visible");
      button.setAttribute("aria-pressed", String(alternate));
      button.setAttribute(
        "aria-label",
        alternate
          ? initialLabel.replace("alternate", "original")
          : initialLabel,
      );
    });
  });

  const mobile = window.matchMedia("(max-width: 767px)");
  const groups = [...document.querySelectorAll(".footer-group")];
  function syncFooter() {
    groups.forEach((group) => {
      const summary = group.querySelector(":scope > summary");
      const restore =
        mobile.matches &&
        group.contains(document.activeElement) &&
        document.activeElement !== summary;
      group.open = !mobile.matches;
      summary.tabIndex = mobile.matches ? 0 : -1;
      if (restore) summary.focus();
    });
  }
  groups.forEach((group) =>
    group
      .querySelector(":scope > summary")
      .addEventListener("click", (event) => {
        if (!mobile.matches) event.preventDefault();
      }),
  );
  syncFooter();
  mobile.addEventListener("change", syncFooter);
})();
