# Phase 4 validation

Executed on 2026-10-13 in WSL Ubuntu. Catalog, content administration, seed data and product details
are implemented. Search/filter controls, the cart, simulated checkout and newsletter submission
await Phase 5 approval. No real payment or order processing exists.

## Delivered

- Product, category, collection, colour, size, variant and product-image models with PostgreSQL
  migrations, publication rules, indexes, unique constraints and pricing/inventory checks.
- Authenticated, permission-aware Django Admin with search, filters, product inlines and stock editing.
- Four image-matched fictional products, thirteen variants, two categories and two collections.
  One sale product and unavailable clothing sizes exercise genuine catalog states.
- `/shop/`, new arrivals, women, men, accessories, category, sale and collection listings; twelve-item
  pagination, product detail pages, related products and database-driven homepage merchandising.
- Validated read-only colour/size/quantity selection using database prices, responsive managed media,
  gallery ordering, product care/fit disclosures, missing-image, unavailable and empty states.
- Bounded staff image validation, complete decoding, metadata stripping and UUID WebP storage paths.
- A repeatable seed command that preserves existing product records, prices, stock and photographs.
  Legacy collection-preview URLs redirect to the new catalog.

## Executed checks

| Check | Actual result |
| --- | --- |
| Catalog migration | Generated and applied successfully to local PostgreSQL |
| Initial seed | Four products created; existing records preserved |
| PostgreSQL pytest suite | **123 passed in 7.25 seconds** |
| Ruff lint / formatting | Passed; all 58 Python files formatted |
| Django system check | No issues; none silenced |
| Migration drift | No changes detected |
| uv dependency consistency | All fifteen installed packages compatible |
| npm audit | Zero reported vulnerabilities in the locked frontend dependencies |
| JavaScript syntax | Navigation and both QA scripts passed |
| Tailwind production build | Passed |
| Production collectstatic | One copied, 155 unmodified, 370 post-processed |
| Production static smoke | Demo page, catalog CSS and three hashed fonts served successfully |
| Django production deployment checks | One expected warning: `security.W004`, HSTS still disabled |

Tests cover draft/scheduled visibility, inactive categories and variants, sold-out states, decimal
pricing, sale eligibility, SKU/option uniqueness, publication and inventory database constraints,
pagination, same-variant colour/size matching, invalid selections, content escaping, admin permissions,
CSRF, upload rejection, metadata-free responsive files, seed preservation and existing foundation controls.
Error pages still render without database queries. In the seeded test dataset, listing rendering takes
five queries and product details/homepage six each, including all related display data.

Pillow 12.3.0 moved from development to runtime requirements; its version did not change. No new
application package or JavaScript framework was added. Python vulnerability auditing is a remaining
deployment task; dependency consistency is not a vulnerability scan.

## Browser checks

Temporary Playwright 1.64.0 and axe Playwright 4.13.0 ran Chromium 156.0.8078.4 outside application
dependencies. The homepage passed at 1440×1000, 1024×900, 768×1024, 390×844 and 320×750. Catalog,
product detail and collection index pages also passed at widths 1440, 1024, 768, 390 and 320 pixels.
Every tested viewport had no horizontal overflow, successful image loads and zero axe violations
under the selected WCAG 2.x A/AA tags. The fourteen supporting/catalog/detail routes scanned by the
homepage script reported zero violations. Browser requests stayed on the local origin, without
unexpected HTTP errors, CSP violations or JavaScript console errors during layout checks.

Verified skip navigation, keyboard menu interaction, Escape/focus return, outside dismissal,
catalog navigation, reduced motion, disabled newsletter and native navigation without JavaScript.
The no-JavaScript product journey followed a card to its detail page, selected an unavailable size,
selected an available size and quantity, and opened the native care disclosure. The bag control
remained disabled. An invalid quantity returned HTTP 400 with a visible error summary and zero axe
violations. Desktop/mobile product screenshots were inspected manually. The first selection QA
attempt expected labels without Django's default colon suffix; labels were refined and the complete
journey passed on rerun.

## Reproduce

Follow README setup: migrate, seed the catalog, build CSS and run the local Django server. QA tooling
can be installed outside the repository:

```bash
npm install --prefix /tmp/maison-elan-browser --no-package-lock --ignore-scripts \
  playwright@1.64.0 @axe-core/playwright@4.13.0 prettier@3.9.10
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  /tmp/maison-elan-browser/node_modules/.bin/playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_homepage.mjs
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_catalog.mjs
```

`MAISON_QA_DIR` and `MAISON_BASE_URL` override the temporary tool location and local server URL.
Original reports/screenshots remain in `.qa/phase-4/`. The reusable QA scripts were updated for
Phase 5 and now write to `.qa/phase-5/`; current reproduction/results are in `phase-5-validation.md`.

To review product management, create your own administrator as described in the README. Edit a
description/price/stock value, check its storefront result, and try draft/future publication. Do not
use genuine customer information or payment details. Seeded size L is unavailable; trousers show
€160.00 with an original illustrative price of €185.00.

## Boundaries

The initial capsule contains four products and one photograph per product. The gallery supports
multiple ordered, optionally colour-associated uploads; no fabricated alternative angles were added.
Categories and collections are managed records; departments remain explicit model choices. Changing
seed identifiers is not a reset or repair workflow. File storage is not transactional with PostgreSQL;
outer rollbacks and retained old media require a reviewed maintenance policy.

Automated axe scans are not WCAG certification. Admin behavior was tested over HTTP for permissions,
forms and CSRF; a rendered-browser admin interaction review remains outstanding. Other browsers,
screen-reader review, Lighthouse measurements, structured data and actual deployed HTTPS/media
security remain Phase 6 work. The production static smoke uses Django's HTTPS test client, not a real
TLS server or hosted database. HSTS and public admin abuse protection remain deployment requirements.
Nothing was committed, pushed, published or deployed. Phase 5 requires owner review and approval.
