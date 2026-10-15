# Storefront refinement and ten-image expansion

The fourteen-product catalog remains current. The later screenshot-led header/footer update is
documented separately in [header/footer validation](header-footer-validation.md); its chrome now
supersedes the restored navigation/footer described in this historical report.

**Restored on 2026-10-15:** at the owner's request, this visual revision is active again after the
later Dior-reference redesign was withdrawn. Warm ivory tokens, Inter typography, the original
“The art of less” hero, static desktop links, full footer and text-based collection index are restored.
All fourteen products and ten added product photographs remain. The withdrawn stylesheet, Jost font
and coastal campaign files are preserved but unused by storefront templates/styles.

Restoration checks: **230 tests passed in 26.66 seconds**, including isolated Admin browser QA;
Ruff passed, Tailwind and hashed static output rebuilt, and Chromium homepage/catalog/detail/
collections/bag/checkout checks passed at 1440/1024/768/390/320px with zero reported axe violations.
The expansion-specific audit verified all ten managed photos, pagination, functional icon links and
centered header geometry. Restored desktop/mobile hero screenshots were visually checked.
Current restoration screenshots/reports live in ignored `.qa/design-restored/chromium/`.

Owner-requested follow-up to Phase 6, executed on 2026-10-14 in WSL Ubuntu.

## Scope and reference

The supplied [Dior collection page](https://www.dior.com/en_cy/fashion/mens-fashion/spring-collection)
was readable through web browsing: product listings, category destinations, item count/filter controls
and editorial interludes were available. Automated Chromium navigation returned HTTP 403, so its
rendered navbar, footer and responsive behavior were not verified. The resulting design is an original
MAISON ÉLAN interpretation of the owner's preferences, using existing brand tokens and fonts.
No Dior photography, logos or proprietary code were imported.

Changes are confined to shared header/footer/icon/product-card templates, catalog listing presentation,
component CSS, image assets, the optional catalog seed expansion, regression checks and documentation.
No database schema changes, application dependencies, authentication or payment features were added.

## Delivered

- Centered serif wordmark with a separate desktop navigation row, native mobile menu and functional
  outline search/bag icons. Targets are 44px; icons have descriptive accessible names. At 320px the
  search destination remains available inside the mobile menu. Search opens its form without JS.
- Three useful footer guidance destinations, four navigation groups, newsletter destination and a
  quieter typographic hierarchy. Demo/privacy disclosures and local currency remain clear.
- Consistent name/color/price product cards, restrained signature badges and a unified count/filter
  toolbar. An original editorial interlude appears only on an unfiltered first page with eight or
  more products. Search, filters and pagination retain their server-rendered behavior.
- Ten distinct, original generated studio photographs, saved as WebP masters in
  `assets/editorial/sources/`, with full prompts and built-in generation mode in
  [provenance](../assets/editorial/provenance.json). Subjects are overshirt, linen shirt, blazer,
  cardigan, silk dress, navy trousers, twill jacket, pleated skirt, turtleneck and scarf.
- `seed_catalog --extended` adds ten matching fictional products using validated managed media,
  variant prices and stock. A fresh expanded catalog has fourteen products, fifty variants, two
  categories and two collections. The local development seed created ten products; existing
  records, image paths, prices and inventory were preserved. Reruns do not reset Admin edits.
- Responsive editorial asset library: 74 WebP derivatives, 2,610,260 bytes total (about 2.49 MiB).
  This is the entire library, not the bytes downloaded by one page. Existing masters are preserved.

## Executed checks

| Check | Result |
| --- | --- |
| Full PostgreSQL pytest suite, including isolated Admin browser test | **230 passed in 64.19 seconds** |
| Ruff lint / format | Passed; 112 Python files formatted |
| Django checks / migration drift | No issues / no changes detected |
| Tailwind build | Passed |
| Chromium homepage/catalog/detail/collections/bag/checkout | Passed at 1440, 1024, 768, 390 and 320px |
| Selected axe WCAG A/AA scans | Zero violations on the checked pages |
| Browser runtime checks | Images loaded; no horizontal overflow or unexpected browser/application CSP errors |
| Keyboard / reduced motion / native forms | Passed |
| JavaScript-disabled shopping journey | Search/filter/sort, add/update/remove, simulated checkout and confirmation isolation passed |
| Expansion-specific checks | All ten distinct photographs loaded; new products searchable; pagination 12/2; icon/footer destinations passed |
| Header geometry | Centered wordmark without utility overlap at 1440/768/390/320px |

The first regression run found three failures because the toolbar changed the established
"Fictional products" disclosure wording; that label was restored before the passing final run.
The expansion QA script's initial sizing-page heading assumption was corrected to the actual
"Finding your fit." heading and its destination is explicitly checked.
The local preview was restarted to clear its template cache and the final disclosure was checked
again. The phone toolbar visually condenses that secondary label; the announcement/footer continue
to disclose the demonstration visibly, and the QA check reads the label's text content.

Screenshots and JSON reports are in ignored `.qa/design-refinement/chromium/`. Earlier Phase 6
storefront screenshots were preserved by giving the existing QA runners an optional output path.
Admin QA exercises pytest's disposable database and test-only user, never a development administrator.

This follow-up was checked in Chromium; Firefox/Safari were not rerun for this revision. Earlier
Phase 6 Firefox results and Lighthouse scores describe the preceding revision. No new Lighthouse
scores are claimed. Automated accessibility scans are not certification; physical assistive-technology
and hosted infrastructure acceptance remain in the deployment handoff.

## Review and reproduce

With the local server running, review `/`, `/shop/`, `/shop/men/`, `/shop/women/`, the second catalog
page, and a new detail such as `/products/wool-overshirt/`. Review the footer and icons at phone size.

```bash
uv run --locked --env-file .env manage.py seed_catalog --extended
npm run css:build
uv run --locked --env-file .env manage.py runserver 127.0.0.1:8000
```

Temporary browser tooling uses the same external install documented in Phase 6. With Chromium
installed under `/tmp/maison-elan-browser/browsers`, run:

```bash
MAISON_QA_OUTPUT=.qa/design-refinement/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_homepage.mjs
MAISON_QA_OUTPUT=.qa/design-refinement/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_catalog.mjs
MAISON_QA_OUTPUT=.qa/design-refinement/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_shopping.mjs
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_design_refinement.mjs
MAISON_BROWSER_QA=1 PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  uv run --locked --env-file .env pytest
```

The expansion-specific browser script expects the seeded fourteen-product demo. Browser submissions
obey real demo rate limits; repeated runs can return 429. No source was committed/pushed and no
public service was deployed. Public activation still requires the owner's deployment approval.
