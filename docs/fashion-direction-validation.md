# Campaign storefront redesign — 2026-10-15

**Withdrawn:** the owner rejected this revision and requested restoration of the preceding design.
This document records historical checks only. The prior warm ivory/Inter design, original hero,
navigation/footer and text-based collection index are restored. The fourteen-product catalog is
preserved; unused campaign, Jost font and stylesheet files remain archived in place.

## Reference inspection and limits

The owner explicitly requested a broader redesign around these references:

- [Dior fashion](https://www.dior.com/en_cy/fashion)
- [Dior men's Spring collection](https://www.dior.com/en_cy/fashion/mens-fashion/spring-collection)

Web browsing retrieved readable campaign and collection content: editorial sections, collection
destinations, product lists, an item count and filter/sort labels. Direct source requests to both
URLs returned **HTTP 403**, each delivering a 755-byte denial document. Those responses and headers
are preserved in ignored `.qa/dior-direction/`. They do not expose Dior's actual component source,
CSS, custom font declarations or menu behavior. No claim is made that those details were inspected,
copied or precisely reproduced. No access-control challenge was bypassed.

The delivered design is an original implementation guided by the owner's stated preferences and
fashion retail interaction patterns. MAISON ÉLAN retains its own name, wordmark, original images,
content and Django shopping architecture. No reference-site assets or source bundles are shipped.

## Delivered behavior

- White surfaces and geometric Jost interface typography, with the existing editorial serif used
  for a larger centered MAISON ÉLAN wordmark. Jost's 26,576-byte variable Latin subset and OFL notice
  are local; the font downloader can fetch one family while preserving the other fonts and manifest.
- A sticky, two-row desktop header with original outline icons and full-width Women/Men/Accessories
  navigation panels. Native disclosures support click and keyboard use without JavaScript. The small
  script adds fine-pointer hover delays, exclusive open panels, Escape/focus return, outside dismissal
  and responsive cleanup. Delayed hover cannot reopen a desktop panel after changing to phone width.
- An original full-width coastal campaign photograph, centered campaign captions, larger paired
  women's/men's category imagery, smaller product captions, seasonal/signature sections and an
  updated brand story/newsletter presentation. The fictional catalog still contains fourteen products.
- An original compact footer, useful guidance destinations, four groups and native accordions.
  JavaScript closes groups on phones while preserving focused content during resizing. Without JS,
  groups begin open and every link remains available.
- Visual collection cards with covers drawn from each collection's latest public product that has
  imagery. Sliced prefetching bounds covers to one product per collection and renders the page in
  **three SQL queries**. Draft/unavailable-for-publication products cannot supply covers; empty
  photography gets an explicit “A new chapter” treatment. No schema migration is needed.
- A separate named `storefront` CSS layer after the retained base/commerce component layers makes
  the redesign reviewable without selector-specificity escalation. Generated CSS is 43,662 bytes
  at the recorded build. No new application package or JavaScript framework was introduced.

Main files: `templates/components/header.html`, `footer.html`, `image.html`, `templates/core/home.html`,
`templates/catalog/collections.html`, `templates/base.html`, `assets/css/app.css`, `storefront.css`,
`static/js/navigation.js`, `apps/core/context_processors.py`, `apps/catalog/views.py` and asset tooling.

## Executed verification

| Check | Actual result |
| --- | --- |
| Full PostgreSQL pytest suite, including isolated Admin browser test | **232 passed in 26.84 seconds** |
| Added collection-cover checks | Public visibility, bounded queries and honest missing-image state passed |
| Ruff lint / formatting | Passed; 113 Python files formatted |
| Django checks / migration drift | No issues / no changes detected |
| Tailwind build | Passed |
| Production-style hashed static build | Passed with build-only dummy configuration and no SQL |
| Homepage / catalog / detail / collections | Chromium passed at 1440, 1024, 768, 390 and 320px |
| Empty/populated bag and demo checkout | Passed at all five widths |
| Selected axe WCAG A/AA scans | Zero violations on the checked pages and open navigation panels |
| Runtime checks | No horizontal overflow, unexpected HTTP, application CSP or JavaScript errors on audited journeys |
| Navigation system | Hover, keyboard, real menu images, exclusivity, Escape/focus, outside dismissal and breakpoint changes passed |
| Mobile footer | Accordion behavior passed at 320/390px |
| JavaScript disabled | Native menus, collections, search/filter/sort, bag editing and simulated checkout passed |
| Other retained checks | Skip link, reduced motion, confirmation session isolation and fictional-only newsletter behavior passed |

Chromium is 156.0.8078.4, Playwright 1.64.0 and axe Playwright 4.13.0. Browser tooling remains in
`/tmp/maison-elan-browser`, outside application dependencies. Existing phase/refinement QA artifacts
were preserved; this revision's screenshots and JSON reports live in `.qa/dior-direction/chromium/`.
Desktop/mobile homepage, open menu, collection and mobile-footer screenshots were visually inspected.

Initial QA work corrected three assumptions: the old hero was no longer the page's first image once
menus gained photography; closed native disclosures defer image loading; and substring menu matching
confused “Men” with “Women”. Image checks now distinguish closed disclosures, explicitly audit open
panel images, and use exact menu labels. Decorative linked menu imagery is explicitly marked as such.
Screenshot review changed duplicate cover selection to use the latest public product per collection.
The hover/breakpoint regression was fixed and reproduced in the browser audit before handoff.

These are local checks. This revision has no new Firefox/Safari, physical screen-reader or Lighthouse
measurement; earlier Lighthouse scores describe older markup/assets. Automated axe results do not
certify WCAG conformance. Real-host TLS, media persistence, backup restore and deployment acceptance
remain in [the deployment handoff](deployment.md). No public service, code push or commit was made.

## Image provenance

The built-in imagegen tool generated `assets/editorial/sources/coastal-campaign.webp`. Its complete
prompt, date and mode are in [the provenance manifest](../assets/editorial/provenance.json). Existing
masters were preserved. Pillow only performs format conversion, metadata removal, resizing and an
art-directed mobile crop; both fictional adult models remain in frame.

The new 1600px desktop WebP is 103,592 bytes and the 800px mobile crop is 45,172 bytes. All nineteen
masters now yield 80 derivatives totaling 2,927,334 bytes. These are library file sizes, not page-load
or field-user performance measurements. Fonts/images are self-hosted and the CSP remains strict.

## Review and reproduce

The local preview runs at `http://127.0.0.1:8000/`. Review the homepage, hover/click/keyboard navigation,
`/shop/`, `/collections/`, and footer disclosures at phone width. The existing expanded seed is
preserved; there is no need to recreate products for this redesign.

```bash
npm run css:build
uv run --locked --env-file .env manage.py runserver 127.0.0.1:8000
MAISON_BROWSER_QA=1 PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  uv run --locked --env-file .env pytest
MAISON_QA_OUTPUT=.qa/dior-direction/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_homepage.mjs
MAISON_QA_OUTPUT=.qa/dior-direction/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_catalog.mjs
MAISON_QA_OUTPUT=.qa/dior-direction/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_shopping.mjs
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_storefront.mjs
```

The prior Phase 6 report documents temporary browser tool installation. The scripts submit fictional
local demo data and obey actual rate limits; repeated runs in one window can return HTTP 429.
