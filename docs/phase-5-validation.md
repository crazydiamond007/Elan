# Phase 5 validation

Executed on 2026-10-14 (Europe/Istanbul) in WSL Ubuntu. Search, filters/sorting, the session bag,
simulated checkout and a local fictional newsletter form are implemented. Phase 6 and deployment
remain subject to owner review. No real payment, retail order or customer delivery information exists.

## Delivered

- Case-insensitive product-name, description and eligible-SKU search with bounded input.
- Managed category, Decimal price-range, size and colour filters; allowed price/newest sorting and
  pagination that retains query parameters. Invalid input gives HTTP 400 with visible field errors.
- Same-variant filter matching, including discounted-variant eligibility on the Sale page. Product
  card prices/options reflect the eligible variants rather than an unrelated lower price.
- CSRF-protected product selection, direct add to demo bag, quantity changes, removal, accurate
  Decimal totals and stock/publication rechecks. Sessions hold variant IDs/quantities only.
- Mobile/desktop bag, empty/unavailable/error feedback and a clearly labelled demo checkout with
  fixed fictional details, no personal-information/payment fields, and explicit acknowledgement.
- Reviewed-price fingerprint, random checkout token, variant row locks, unique-token demo receipts,
  idempotent confirmation and private session-bound confirmation URLs. Stock remains unchanged.
- Local reserved-address newsletter signup with validation, normalization, duplicate-safe persistence
  and consistent success feedback. No email is sent; genuine addresses are rejected.
- Shared PostgreSQL fixed-window abuse counters for cart/checkout/newsletter POST endpoints, hashed
  client keys, HTTP 429/Retry-After responses and an expired-counter maintenance command.
- Admin visibility for fictional signups and read-only demo receipts under model permissions.
- Updated architecture, privacy disclosures, setup/review workflow and production limitations.

## Executed checks

| Check | Actual result |
| --- | --- |
| New migrations | Applied for core counters, demo receipts and demo signups; receipt total bound adjusted |
| PostgreSQL pytest suite | **204 passed in 14.26 seconds** |
| Ruff lint and formatting | Passed; 94 Python files formatted |
| Django system checks | No issues; none silenced |
| Migration drift | No changes detected |
| uv dependency consistency | All fifteen installed packages compatible |
| npm audit | Zero reported vulnerabilities in the locked frontend dependencies |
| Tailwind CSS build | Passed |
| Production collectstatic | One copied, 155 unmodified, 370 post-processed |
| Production static smoke | Disclosure page, hashed shopping/filter CSS and three hashed fonts served |
| Production deployment check | One expected warning: `security.W004`; HSTS awaits verified deployment HTTPS |
| JS syntax | Navigation and all three browser QA scripts passed |

No Python/JavaScript application dependency was added or upgraded. Existing lockfiles remain valid.
Dependency consistency does not constitute Python vulnerability auditing; that remains Phase 6 work.

The suite includes publication/permissions/upload/foundation regressions plus search escaping,
same-variant price/colour/size/sale matching, invalid/duplicate parameters, retained pagination,
add/update/remove, malformed session input, capacity/quantity limits, stock conflicts, current prices,
CSRF, private cache headers, checkout acknowledgement/tokens, price-review invalidation, no stock
decrement, session isolation, repeated receipt submissions and newsletter validation/no-email behavior.

Concurrent PostgreSQL tests verify that ten requests against a shared limit of three allow exactly
three, and that two simultaneous checkout submissions create one receipt and return one confirmation.
Cart snapshots use two queries regardless of line count; catalog rendering uses seven in the seeded
dataset and home/detail rendering six. Generic 500 rendering still requires zero database queries.

An added capacity test initially chose a sold-out seed variant and reached the stock error first.
The fixture was corrected to choose an in-stock variant and use distinct bounded IDs; the complete
suite passed on rerun. Review also caught and fixed cross-variant Sale filtering before final checks.

## Browser checks

Used temporary Playwright 1.64.0, axe Playwright 4.13.0 and Chromium 156.0.8078.4 outside application
dependencies. Homepage checks passed at 1440×1000, 1024×900, 768×1024, 390×844 and 320×750. Catalog,
product and collection screens passed at widths 1440, 1024, 768, 390 and 320. Empty bag, populated bag
and checkout passed at the same five widths. Tested pages had no horizontal overflow, unsuccessful
image loads or axe violations under selected WCAG 2.x A/AA tags. Normal layout journeys produced no
unexpected HTTP, JavaScript or CSP errors and used only local-origin visitor assets.

Verified the complete no-JavaScript journey: search/filter/sort, follow a product, add two units,
update to one, remove, add the sale trousers, acknowledge demo checkout, complete confirmation and
return to the empty bag. A separate browser session received HTTP 404 for the confirmation URL.
Newsletter signup with `browser-qa@example.com` succeeded locally; a genuine-domain submission was
rejected with HTTP 400. Newsletter success/error and invalid price-filter pages reported zero axe
violations at 390px. Desktop bag and mobile checkout screenshots were inspected. Mobile header and
summary placement were refined, then the homepage/shopping checks passed again.

Local browser QA created fictional receipts and one reserved-address signup record. These contain
no actual customer information and no external service was contacted. They are intentionally local
runtime data; nothing was committed, pushed, published or deployed.

## Reproduce optional browser QA

Follow README setup and start the loopback Django server after migrations, catalog seeding and CSS
build. Install QA tools outside the repository if needed:

```bash
npm install --prefix /tmp/maison-elan-browser --no-package-lock --ignore-scripts \
  playwright@1.64.0 @axe-core/playwright@4.13.0 prettier@3.9.10
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  /tmp/maison-elan-browser/node_modules/.bin/playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_homepage.mjs
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_catalog.mjs
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_shopping.mjs
```

`MAISON_QA_DIR` and `MAISON_BASE_URL` override the temporary QA directory/server. Original output is
under `.qa/phase-5/`; reusable scripts now target Phase 6 engine-specific folders. Current reproduction
is in `phase-6-validation.md`. QA obeys real abuse limits; repeated shopping runs within ten minutes
can receive HTTP 429. Do not disable protection to bypass that result.

For manual review, try `/shop/?q=coat&size=m&color=charcoal&sort=price-asc`, select M and add a piece,
edit `/bag/`, then complete `/checkout/`. Confirm the receipt says no payment/real order and that the
catalog's stock remains unchanged. Use `guest@example.com` at `/newsletter/` rather than real input.
Admin stock/price changes can demonstrate revalidation; preserve your preferred catalog edits.

## Limits and Phase 6

The standard database session backend retains last-write-wins behavior for simultaneous independent
cart edits. Unique checkout tokens are tested under duplicate submissions, but that does not imply
atomic multi-tab cart merging. Review the desired concurrent-edit policy before public exposure.
Fixed-window IP limits have boundary bursts and cannot prevent distributed abuse; trusted proxy
client-address handling, admin login protection and infrastructure controls remain required.

Expired rate counters need scheduled `prune_rate_limits`; expired Django sessions need `clearsessions`.
Receipts and fictional signups remain until owner removal. No retention automation is implied. A
confirmation requires its originating session; expired/rotated sessions or changed signing secrets
can make old links inaccessible. No customer accounts or order-history feature is introduced.

Production static smoke used Django's HTTPS test client, without a real TLS server or hosted database.
Separate media hosting, orphan-file retention, HTTPS/proxy/HSTS review, dependency auditing, rendered
Admin/browser review, additional browsers, screen readers, SEO/structured data and measured Lighthouse
checks remain Phase 6. Automated axe results are not WCAG certification or a security guarantee.
