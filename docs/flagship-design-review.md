# Flagship design refinement — 2026-10-15

This is the first reviewable pass of the competitive design assessment. The wordmark and reusable
product-page components are implemented, with the Sculpted Wool Coat as the first fully illustrated
example. Collection landing pages, listing-card enhancements, filter chips, bag feedback and the
remaining photography batch are later passes pending this visual review. No deployment or push.

## Visual direction

- Retain the warm ivory, limestone and charcoal palette, original homepage campaign, self-hosted
  Inter/Cormorant pairing and single-row navigation.
- The typographic signature makes ÉLAN the primary name, with a small, spaced MAISON above.
  This uses the existing licensed fonts; it is not a bespoke typeface or an exclusive-logo claim.
  The large footer wordmark stays removed.
- Product titles use balanced serif line breaks and a narrower measure. Copy, prices and option
  labels use the interface sans serif. Purchasing states have explicit selected, unavailable,
  quantity-error and keyboard-focus treatments.
- Photograph the garment as an object, on a model, from behind and at tactile detail scale. Keep
  construction and colour consistent. Warm daylight, matte textiles and architectural settings
  connect products to the homepage. Product shots need full hems/sleeves; close views should reveal
  a construction detail. No baked-in lettering or reference-brand assets.

## Delivered behavior

The coat has four managed photographs: the original front plus three generated views. Thumbnail
navigation, a current-image count and native-dialog enlargement support full-size/fit modes,
scrollable high-resolution detail, previous/next controls, Escape, bounded Tab navigation and focus
restoration. Arrow keys switch photographs in fitted mode and pan the focused photograph in full-size
mode. On mobile, the gallery precedes
purchasing controls. Without JavaScript, photographs stay visible, thumbnails jump to images and
image links open the full photograph.

JavaScript enhances the validated colour/size selects into labelled colour choices and size radios.
An escaped JSON snapshot of active database variants supplies immediate price/availability feedback.
Unavailable sizes are explicit; invalid quantities disable adding. The original CSRF-protected bag
endpoint revalidates prices, active variants and stock. A browser snapshot reserves nothing and
cannot determine an accepted price. Server-side errors retain the native controls/error summary.
No new API or frontend dependency was introduced.

`Product.styled_with` is an optional directed relationship managed by native checkboxes in Admin.
Curated public companions appear under “Wear it with”; uncurated products retain category suggestions
under “Explore also.” Non-public companions and the current product are excluded. One additional
bounded SQL query supports the relationship; tests cover 11 queries on a first detail request and
8 with an existing shopping session.

`seed_editorial` adds missing coat photographs and initial outfit links. It preserves occupied image
positions, existing images, curation, prices and stock. Run `seed_catalog` first on a fresh database.
The additive migration and seed were applied to the local development database.

## Original assets

Built-in imagegen used our existing coat master as the garment reference. Selected outputs were
visually reviewed and saved as metadata-free WebP masters using Pillow. They illustrate fictional
garments, not manufacturing evidence. Runtime responsive copies use the validated ProductImage pipeline.

- `assets/editorial/sources/coat-styled.webp`
- `assets/editorial/sources/coat-back.webp`
- `assets/editorial/sources/coat-detail.webp`

The complete final prompts, mode and reference are in
[flagship provenance](../assets/editorial/flagship-provenance.json).

## Executed checks

| Check | Actual result |
| --- | --- |
| Full PostgreSQL suite, including isolated Admin browser test | 233 passed in 29.19 seconds |
| Django checks / migration drift | No issues / no changes detected |
| Ruff lint / formatting | Passed |
| Tailwind compilation | Passed |
| Production hashed static build | Passed, including the new script and compiled CSS |
| Homepage / supporting-page browser audit | Passed at 1440/1024/768/390/320px |
| Catalog, product and collection audit | Passed at all five widths, including no-JavaScript selection |
| Demo bag, checkout and newsletter journeys | Passed, including no-JavaScript checkout |
| New gallery/selection audit | Four images, all thumbnails, quantity bounds, unavailable size, enlargement, keyboard/focus and zero axe violations at all five widths |

Chromium 156.0.8078.4 was used. Reports/screenshots are in ignored `.qa/flagship/chromium/`.
The Admin test caught an unlabelled internal field in the new multi-select autocomplete; native
checkboxes resolved it. The modal test waits for asynchronous native close/focus events. Product
desktop/mobile captures and generated garment views were visually inspected. These checks are not
WCAG certification. New Lighthouse measurements, Safari/iOS and assistive-technology testing were
not performed for this pass.

## Completion checks — 2026-10-16

After the interrupted session, the owner restarted the existing PostgreSQL cluster. The local
Django preview was restarted and the temporary browser tools restored without changing application
dependencies. The final viewer audit passed again at all five widths, including the new full-size
mode: the image grows beyond its fitted height, the scroll area receives focus, ArrowDown pans it,
and ArrowRight preserves the current photograph while enlarged. Fit mode restores photo navigation;
Escape returns focus to the visible gallery image. Both zoom states reported zero axe violations,
and the audit recorded no browser errors.

Django checks, migration-drift detection, Ruff, JavaScript syntax/formatting, Tailwind compilation,
the production hashed static build and `git diff --check` passed. The 233-test PostgreSQL result above
is from 2026-10-15; subsequent changes concern the image viewer and its browser audit. The preview
is available at `http://127.0.0.1:8000/`. Changes remain local for the owner's visual review.

## Review locally

Visit `/` for the wordmark and `/products/sculpted-coat/` for the flagship. Select M, inspect the
unavailable L, try a quantity above stock, explore every photo and use the enlarged viewer with the
keyboard. Add a valid size to the demo bag. Check the “Wear it with” selection below.

```bash
uv run --locked --env-file .env python manage.py migrate
uv run --locked --env-file .env python manage.py seed_editorial
npm run css:build
uv run --locked --env-file .env python manage.py runserver 127.0.0.1:8000
```

The browser tools remain outside application dependencies:

```bash
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_flagship.mjs
```
