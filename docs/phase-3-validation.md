# Phase 3 validation

Executed on 2026-10-13 in WSL Ubuntu. This phase adds the design system and editorial presentation;
it does not implement a database catalog, cart, checkout or newsletter submission.

## Automated checks

| Check | Actual result |
| --- | --- |
| Django system checks | No issues, none silenced |
| Migration consistency | No changes detected; no Phase 3 schema changes |
| PostgreSQL-backed pytest suite | **66 passed in 1.32 seconds** |
| Ruff lint / format | Passed |
| JavaScript syntax checks | Navigation and browser QA scripts passed |
| Tailwind production CSS build | Passed; current component stylesheet generated |
| Responsive image build | 19 WebP derivatives, approximately 1.4 MiB combined |
| Production `collectstatic` | 29 copied, 127 unmodified, 397 post-processed |
| Production static smoke | Current CSS, three hashed font faces, images and navigation script all served |

The tests include all public routes, internal links and fragments, meaningful department previews,
safe error responses, local responsive image resources, readonly endpoints and the disabled newsletter.
Existing permission, session, CSRF and production-configuration tests still pass.

## Browser checks

Used temporary Playwright **1.64.0**, axe Playwright **4.13.0**, and Chromium **156.0.8078.4**.
These packages are not application dependencies. Prettier **3.9.10** was also used as temporary tooling.

| Viewport | Horizontal overflow | Browser errors | axe violations |
| --- | --- | --- | --- |
| 1440 × 1000 | None | None | 0 |
| 1024 × 900 | None | None | 0 |
| 768 × 1024 | None | None | 0 |
| 390 × 844 | None | None | 0 |
| 320 × 750 | None | None | 0 |

The eight supporting preview/information routes also reported zero violations under the selected
`wcag2a`, `wcag2aa`, `wcag21aa` and `wcag22aa` axe tags. All homepage images were loaded before
full-page screenshots. Visitor asset requests stayed on the local origin.

Verified the skip link, keyboard opening/tabbing, Escape dismissal and focus return, outside-click
dismissal, fragment focus, Women navigation, reduced-motion styles, disabled newsletter controls,
and native Men navigation with JavaScript disabled. Desktop and mobile screenshots were inspected.

A first browser run caught a stale Phase 2 watcher overwriting the current CSS. That process was
stopped, the CSS rebuilt, and a computed-style guard added to QA. Full-page captures initially omitted
lazy images; QA now scrolls through the page and waits for successful image loads before screenshots.

## Reproduce optional browser QA

The recorded results below describe Phase 3. The reusable homepage QA script was updated for
database catalog destinations in Phase 4; current reproduction/results are in `phase-4-validation.md`.
Start the local server and build CSS as documented in the README. Install QA tooling outside the repo:

```bash
npm install --prefix /tmp/maison-elan-browser --no-package-lock --ignore-scripts \
  playwright@1.64.0 @axe-core/playwright@4.13.0 prettier@3.9.10
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  /tmp/maison-elan-browser/node_modules/.bin/playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  node scripts/qa_homepage.mjs
```

`MAISON_QA_DIR` and `MAISON_BASE_URL` optionally override the QA installation and local server URL.
The original results and screenshots are in the ignored `.qa/phase-3/` directory; current script
output uses `.qa/phase-4/`. The preview remains at
<http://127.0.0.1:8000/>. The code does not weaken the site's CSP to run QA.

## Limits and next phase

Automated axe results and these browser checks are not a WCAG conformance certification. Screen-reader
review, additional browsers, Lighthouse benchmarks and deployed HTTPS/security review remain in Phase 6.
The production static smoke uses Django's test client with HTTPS settings, not a real TLS deployment.
HSTS and public admin abuse protection remain deployment tasks documented in `security.md`.

The four pieces and their prices are temporary, explicitly fictional editorial fixtures. Newsletter
controls are disabled and have no submission form. Phase 4 will introduce catalog models, migrations,
admin content management, seed data and actual product listing/detail routes after owner approval.
