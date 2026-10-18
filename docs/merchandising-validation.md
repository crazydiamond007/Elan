# Merchandising refinement — 2026-10-17

The owner requested that the existing stage be committed and pushed before implementing the next
approved design improvements. Checkpoint
[`2fc7657`](https://github.com/crazydiamond007/Elan/commit/2fc76578a15e4fb996eabf955e5aaa9a20371ec8)
was pushed to `origin/master` first. The changes described here are the subsequent local review pass.

## Result

1. Collection index cards and collection details now lead with managed photographs. A nullable
   `Collection.cover_image` field and Admin autocomplete let the owner select a product image.
   A public-product existence annotation hides unpublished/ineligible source imagery without
   per-collection queries; missing covers receive a typographic index placeholder.
2. Product cards preview a second photograph of the same colour on hover or keyboard focus, with
   a separate 44px toggle for touch and keyboard use. Card names reserve two lines; sale pieces
   show the original price associated with the displayed minimum-price variant.
3. Fifteen new original photographs give the knit, tote, overshirt, blazer and cardigan styled,
   back and material-detail views. Together with the existing coat, six products have four views.
   The established gallery enlargement, keyboard controls and responsive media pipeline are reused.
4. The seasonal homepage campaign now uses the first eligible featured collection cover and its
   destination, distinct from the category portrait. Initial knit/blazer covers use 3:4 frames
   that preserve the complete styled composition. The original homepage hero remains in place.
5. The purchasing column has tighter description, option and disclosure spacing, with shorter helper
   copy. Native selection forms, stock validation and visible demo disclosure remain available.
6. Four desktop footer columns become collapsible mobile groups below 768px. Resizing opens desktop
   groups and restores focus before closing a focused mobile group. Native details remain usable
   without JavaScript; the fallback starts open so all footer destinations remain visible.
7. A bounded session quantity badge accompanies the bag icon. After an accepted addition, the existing
   server-rendered redirect shows product, colour, size and added quantity in a restrained feedback
   panel. Prices and availability still come from the server; no asynchronous commerce API was added.

`0003_collection_cover_image` was applied to the local database. `seed_merchandising` added fifteen
photos and initial missing covers/outfit links, preserving occupied image positions and existing
prices, stock, covers and curation. It validates required assets/products/front colours before writing.
See [asset provenance](asset-licenses.md) and the versioned generation prompts for the image sources.
No application dependency, payment integration or public deployment was introduced.

## Executed checks

- Full PostgreSQL suite, including the optional Admin browser test: **238 passed in 38.74 seconds**.
  Added tests cover hidden cover sources, matching-colour card imagery, original-price rendering,
  safe repeat seeding, preservation of owner content/inventory and session-isolated bag feedback.
  The error-page regression was then strengthened to reject any session load while rendering a
  matched-route 500 response; the affected public-page module passed again: **22 passed in 0.61s**.
- Existing bounded-query checks pass: catalog listing **7** queries, first product detail **11**,
  returning product detail **8**, and returning homepage **8**. The homepage budget rises from six
  for one campaign query and one existing-session read needed by the new badge. Image-card properties
  use prefetched data and do not query per card.
- Chromium **156.0.8078.4**: homepage, catalog, collections, flagship product, empty/populated bag
  and checkout audited at **1440, 1024, 768, 390 and 320px**, without horizontal overflow, browser
  errors or reported axe WCAG A/AA violations in those tested states. Existing keyboard, reduced-motion,
  invalid selection and no-JavaScript shopping/newsletter checks passed.
- The focused merchandising audit additionally passed hover/focus/keyboard previews, touch toggling,
  image-led collection details at desktop/mobile sizes, all six four-view galleries at 320px,
  mobile footer keyboard/resize focus behavior, persistent/cleared bag counts and detailed item feedback.
  Twelve additional audited states reported zero axe violations. These checks are not accessibility
  certification or a comprehensive real-device browser matrix.
- The fifteen-image contact sheet, collection index, mobile product page, desktop/mobile campaign
  and mobile footer captures were visually reviewed for garment consistency, framing and spacing.
- Django system checks, migration-drift check, Ruff lint/format checks, JavaScript syntax/format
  checks, Tailwind compilation and production hashed static collection passed.

Reports/screenshots live under ignored `.qa/merchandising/chromium/`; the existing flagship script
writes to `.qa/flagship/chromium/`. Browser dependencies remain outside application lockfiles in
`/tmp/maison-elan-browser`. The focused script is versioned at `scripts/qa_merchandising.mjs`.

An initial suite run exposed the expected homepage query-budget increase; its assertion was updated
to the measured eight queries, then the complete suite passed. No business-logic failure was hidden.

## Reproduce and review

After normal environment setup, with PostgreSQL running:

```bash
uv run --locked --env-file .env manage.py migrate
uv run --locked --env-file .env manage.py seed_catalog --extended
uv run --locked --env-file .env manage.py seed_editorial
uv run --locked --env-file .env manage.py seed_merchandising
npm run css:build
uv run --locked --env-file .env manage.py runserver 127.0.0.1:8000
```

Review `/`, `/collections/`, `/collections/autumn-winter-26/`, `/shop/`,
`/products/fine-wool-knit/` and `/products/sculpted-coat/`. Add a selected variant to the demo bag,
follow the detailed confirmation, then navigate home to check the count. At mobile width, expand
footer sections and use the product-card photo button. Choose collection covers in Admin.

With the optional browser tooling described in the earlier validation records installed externally:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  MAISON_BROWSER_QA=1 uv run --locked --env-file .env pytest
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  node scripts/qa_merchandising.mjs
```

Runtime media is not committed; fresh installations recreate it through the seed commands. Products
outside the six signature examples retain single photographs. Live deployment, cross-device manual
accessibility review and production media/HTTPS validation remain separate work.
