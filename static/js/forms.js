/* Native forms remain functional without JS; focus and pending feedback enhance them. */
(() => {
  const error = document.querySelector('main [role="alert"]');
  if (error) {
    error.tabIndex = -1;
    error.focus();
  }
  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (form.dataset.pending === "true") {
      event.preventDefault();
      return;
    }
    form.dataset.pending = "true";
    form.setAttribute("aria-busy", "true");
    if (event.submitter) event.submitter.setAttribute("aria-disabled", "true");
  });
  window.addEventListener("pageshow", () => {
    for (const form of document.querySelectorAll('form[data-pending="true"]')) {
      delete form.dataset.pending;
      form.removeAttribute("aria-busy");
    }
    for (const button of document.querySelectorAll('[aria-disabled="true"]')) {
      button.removeAttribute("aria-disabled");
    }
  });
})();
