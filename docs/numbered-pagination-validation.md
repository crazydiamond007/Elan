# Numbered pagination and page titles

Implemented on 2026-10-16 from the owner's pagination screenshot and linked Dior collection page.
The screenshot provides the control arrangement; the storefront retains its own ivory, off-white,
charcoal, typography and outline icons. The reference page was retrieved at
https://www.dior.com/en_cy/fashion/womens-fashion/autumn-winter-collection and exposes a plain
collection heading. This does not claim to reproduce its interactive pagination.

## Changes

- A lightly outlined rounded pagination panel contains a small “Product catalogue · Demo” label,
  Previous/Next pills, numbered page circles and a separate “Showing page X of Y” status line.
- The active page uses charcoal fill and `aria-current="page"`. Other numbers link directly to
  server-rendered pages and retain current filters/sorting. Previous/Next use `rel` attributes.
- At boundaries, unavailable directions remain non-interactive spans marked `aria-disabled`.
  Every actionable control has a 44px minimum height. Controls have keyboard focus indicators.
- Django's bounded elided page range supplies numbers and ellipses for longer catalogs, without
  adding database queries. Mobile layouts allow the longer number group to occupy its own row.
- Template browser titles use `Page name | MAISON ÉLAN`; the homepage uses
  `MAISON ÉLAN | A considered wardrobe`. Product social titles and the default social title also
  use a vertical bar. The visible page headings are unchanged. Existing owner edits that had
  removed dashes and left double spaces were normalized to this format.

## Executed checks

- Affected PostgreSQL suite: **99 passed in 9.17 seconds**, covering catalog/pagination, filtering,
  metadata, public pages and editorial rendering. An existing copy assertion was updated to check
  the new numbered links and current-page label.
- Chromium at **1920, 1440, 1024, 768, 390 and 320px**: first/last page controls aligned, current
  states correct, disabled directions non-interactive, direct-number/Previous/Next navigation
  functional, filter/sort parameters preserved, no horizontal overflow and zero reported axe
  violations. Representative public/private/error browser titles and public social titles contain
  no em dashes. Desktop/mobile captures were visually reviewed.
- Ruff, Python formatting, CSS/JavaScript formatting, Tailwind compilation, the production hashed
  static build and `git diff --check` passed. No runtime dependency was added.

Reports/screenshots live in ignored `.qa/numbered-pagination/`. The temporary browser audit is
`/tmp/maison-pagination-review.mjs`. Browser tooling remains outside the application lockfiles.
An initial audit used an unnecessary locator timeout for intentionally absent private-page metadata;
the final audit checks whether the metadata exists before reading it.

Review at `http://127.0.0.1:8000/shop/`. Changes remain local; no commit, push or deployment occurred.
