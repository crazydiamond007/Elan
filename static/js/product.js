/* Progressive product selection and gallery. Django validates every bag submission. */
(() => {
  const form = document.getElementById("variant-selection");
  const payload = document.getElementById("product-options");
  if (!form || !payload) return;
  const options = JSON.parse(payload.textContent);
  const color = form.elements.color;
  const size = form.elements.size;
  const quantity = form.elements.quantity;
  const visual = form.querySelector("[data-visual-options]");
  const purchase = document.querySelector(".purchase-preview");
  const price = document.querySelector("[data-detail-price]");
  const availability = document.querySelector("[data-availability]");
  const gallery = document.querySelector("[data-product-gallery]");
  const photos = [...gallery.querySelectorAll("[data-gallery-photo]")];
  const thumbnails = [...gallery.querySelectorAll("[data-gallery-thumbnail]")];
  let visiblePhotos = [];
  let current = 0;

  function showPhotograph(index) {
    current = Math.max(0, Math.min(index, visiblePhotos.length - 1));
    for (const photo of photos) photo.hidden = photo !== visiblePhotos[current];
    thumbnails.forEach((thumbnail, index) => {
      const available =
        !thumbnail.dataset.color || thumbnail.dataset.color === color.value;
      thumbnail.hidden = !available;
      if (photos[index] === visiblePhotos[current])
        thumbnail.setAttribute("aria-current", "true");
      else thumbnail.removeAttribute("aria-current");
    });
    gallery.querySelector("[data-gallery-empty]").hidden =
      visiblePhotos.length > 0;
    gallery.querySelector("[data-gallery-counter]").textContent =
      visiblePhotos.length
        ? `${current + 1} / ${visiblePhotos.length}`
        : "Photography coming soon";
  }

  function updateGallery() {
    visiblePhotos = photos.filter(
      (photo) => !photo.dataset.color || photo.dataset.color === color.value,
    );
    showPhotograph(0);
  }

  function group(name, choices, select) {
    const fieldset = document.createElement("fieldset");
    fieldset.className = `visual-option visual-${name}`;
    const legend = document.createElement("legend");
    legend.textContent = name === "color" ? "Colour" : "Size";
    fieldset.append(legend);
    const items = document.createElement("div");
    items.className = "option-items";
    for (const choice of choices) {
      const label = document.createElement("label");
      label.className = "option-choice";
      const input = document.createElement("input");
      input.type = "radio";
      input.name = `visual_${name}`;
      input.value = choice.value;
      const text = document.createElement("span");
      text.textContent = choice.label;
      if (name === "color") {
        const swatch = document.createElement("span");
        swatch.className = "colour-swatch";
        swatch.dataset.swatch = choice.value;
        swatch.setAttribute("aria-hidden", "true");
        text.prepend(swatch);
      }
      label.append(input, text);
      items.append(label);
      input.addEventListener("change", () => {
        select.value = input.value;
        if (name === "color") {
          const matching = options.variants.filter(
            (variant) => variant.color === color.value,
          );
          if (
            !matching.some(
              (variant) => variant.size === size.value && variant.maximum > 0,
            )
          )
            size.value =
              (matching.find((variant) => variant.maximum > 0) || matching[0])
                ?.size || "";
          updateGallery();
        }
        updateSelection();
      });
    }
    fieldset.append(items);
    visual.append(fieldset);
  }

  function updateSelection() {
    const variant = options.variants.find(
      (item) => item.color === color.value && item.size === size.value,
    );
    visual.querySelectorAll("input").forEach((input) => {
      const isSize = input.name === "visual_size";
      input.checked = input.value === (isSize ? size.value : color.value);
      input.disabled =
        isSize &&
        !options.variants.some(
          (item) =>
            item.color === color.value &&
            item.size === input.value &&
            item.maximum > 0,
        );
      input.setAttribute(
        "aria-label",
        `${(isSize ? options.sizes : options.colors).find((choice) => choice.value === input.value).label}${input.disabled ? " — unavailable" : ""}`,
      );
    });
    if (variant) {
      price.textContent = `€${variant.price}`;
      if (variant.original) {
        const original = document.createElement("span");
        original.className = "original-price";
        const prefix = document.createElement("span");
        prefix.className = "visually-hidden";
        prefix.textContent = "Original price ";
        const amount = document.createElement("s");
        amount.textContent = `€${variant.original}`;
        original.append(prefix, amount);
        price.append(original);
      }
      availability.textContent =
        variant.maximum > 0
          ? "Available in the demo catalog"
          : "This size is currently unavailable";
      const details = document.createElement("span");
      details.textContent = `${color.selectedOptions[0].textContent} / ${size.selectedOptions[0].textContent} · SKU ${variant.sku}`;
      availability.append(details);
    } else
      availability.textContent =
        "This colour and size combination is unavailable.";
    // Quantity errors remain visible and editable; never silently change the requested quantity.
    const enough =
      variant &&
      Number.isInteger(quantity.valueAsNumber) &&
      quantity.valueAsNumber >= 1 &&
      quantity.valueAsNumber <= variant.maximum;
    purchase.disabled = !enough;
    purchase.textContent = enough
      ? "Add to demo bag"
      : variant?.maximum > 0
        ? "Check quantity"
        : "Currently unavailable";
  }

  const enhanceSelection = !form.querySelector(".form-errors");
  if (enhanceSelection) {
    group("color", options.colors, color);
    group("size", options.sizes, size);
    form
      .querySelectorAll("[data-native-option]")
      .forEach((field) => (field.hidden = true));
    visual.hidden = false;
    form.querySelector(".selection-actions button").hidden = true;
    form.querySelector("#selection-help").textContent =
      "Unavailable sizes are marked. Prices are illustrative.";
    quantity.addEventListener("input", updateSelection);
  }
  gallery.classList.add("gallery-enhanced");
  thumbnails.forEach((thumbnail, index) =>
    thumbnail.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
        return;
      event.preventDefault();
      showPhotograph(visiblePhotos.indexOf(photos[index]));
    }),
  );
  updateGallery();
  if (enhanceSelection) updateSelection();

  const viewer = document.querySelector("[data-image-viewer]");
  if (!viewer?.showModal) return;
  let opener;
  const zoom = viewer.querySelector("[data-viewer-zoom]");
  const frame = viewer.querySelector("figure");
  frame.setAttribute(
    "aria-label",
    "Product photograph; scroll to explore full-size detail",
  );
  zoom.addEventListener("click", () => {
    const enlarged = viewer.classList.toggle("viewer-zoomed");
    zoom.setAttribute("aria-pressed", String(enlarged));
    zoom.textContent = enlarged ? "Fit to screen" : "View full size";
    frame.tabIndex = enlarged ? 0 : -1;
    if (enlarged) frame.focus();
  });
  function updateViewer() {
    viewer.classList.remove("viewer-zoomed");
    frame.tabIndex = -1;
    frame.scrollTop = 0;
    frame.scrollLeft = 0;
    zoom.setAttribute("aria-pressed", "false");
    zoom.textContent = "View full size";
    const photo = visiblePhotos[current];
    const image = photo.querySelector("img");
    const enlarged = viewer.querySelector("[data-viewer-image]");
    enlarged.src = photo.href;
    enlarged.alt = image.alt;
    viewer.querySelector("[data-viewer-caption]").textContent = image.alt;
    viewer.querySelector("[data-viewer-count]").textContent =
      `${current + 1} / ${visiblePhotos.length}`;
    viewer
      .querySelectorAll("[data-viewer-previous], [data-viewer-next]")
      .forEach((button) => (button.disabled = visiblePhotos.length < 2));
  }
  function step(direction) {
    showPhotograph(
      (current + direction + visiblePhotos.length) % visiblePhotos.length,
    );
    updateViewer();
  }
  photos.forEach((photo) =>
    photo.addEventListener("click", (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)
        return;
      event.preventDefault();
      opener = photo;
      updateViewer();
      viewer.showModal();
      document.documentElement.classList.add("drawer-open");
      viewer.querySelector("[data-viewer-close]").focus();
    }),
  );
  viewer
    .querySelector("[data-viewer-close]")
    .addEventListener("click", () => viewer.close());
  viewer
    .querySelector("[data-viewer-previous]")
    .addEventListener("click", () => step(-1));
  viewer
    .querySelector("[data-viewer-next]")
    .addEventListener("click", () => step(1));
  viewer.addEventListener("keydown", (event) => {
    if (
      !viewer.classList.contains("viewer-zoomed") &&
      (event.key === "ArrowLeft" || event.key === "ArrowRight")
    ) {
      event.preventDefault();
      step(event.key === "ArrowLeft" ? -1 : 1);
    }
    if (event.key === "Tab") {
      const buttons = [
        ...viewer.querySelectorAll('button:not([disabled]), [tabindex="0"]'),
      ];
      if (event.shiftKey && document.activeElement === buttons[0]) {
        event.preventDefault();
        buttons.at(-1).focus();
      } else if (!event.shiftKey && document.activeElement === buttons.at(-1)) {
        event.preventDefault();
        buttons[0].focus();
      }
    }
  });
  viewer.addEventListener("close", () => {
    if (!document.querySelector("dialog[open]"))
      document.documentElement.classList.remove("drawer-open");
    (opener && !opener.hidden ? opener : visiblePhotos[current])?.focus({
      preventScroll: true,
    });
  });
})();
