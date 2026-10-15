# Screenshot-led header, drawers and footer — 2026-10-15

The owner supplied four screenshots showing a single-row header, a left menu drawer, a right search
drawer and a spacious footer with serif headings/newsletter. This focused implementation uses those
visual references while retaining MAISON ÉLAN's restored homepage imagery, Inter/Cormorant fonts,
warm catalog styling, fourteen products and existing shopping behavior. No reference-site logo,
photography, copied source code or new dependency was introduced.

## Delivered

- One white header row with a menu control at every viewport, centered brand wordmark and working
  search/bag icons. The old desktop navigation row and “The maison” link are removed. Small-phone
  utility spacing keeps the wordmark centered without overlapping the 44px targets.
- A left navigation drawer with close control, current catalog destinations and secondary links.
  Without JavaScript, native details expose the navigation below the header and remain closable
  through the menu summary.
- A separate right search drawer with a labelled GET form, suggestions and three actual product
  previews where the current page already supplies products. Elsewhere it shows clearly labelled
  editorial category destinations. It reuses cached view data after the main content, with no new
  API, browser fetch, global product query or N+1 image access. Existing query bounds still pass.
  Without JavaScript, the search icon opens the existing server-rendered catalog search form.
- Native modal dialogs provide backdrop/inert-page behavior. The script handles Escape, close and
  outside dismissal, trigger focus restoration, scroll locking and explicit Tab/Shift-Tab cycling.
  Close controls stay visible while a drawer scrolls. Search uses a reinforced underline for focus;
  other controls retain their visible focus outlines. Dialog styling respects existing reduced motion.
- A white footer with three meaningful service links, four serif-headed link groups, working privacy/
  demo-shopping disclosures and a reserved-address newsletter form. The large footer wordmark is gone;
  the small copyright identity remains. Newsletter branding now says “Stay inspired with ÉLAN”.
- The existing newsletter component moved from homepage main content into the footer. It is omitted
  on private shopping/marketing pages and unresolved error contexts to avoid duplicate forms and
  distractions. The dedicated newsletter page retains its existing feedback, CSRF validation,
  fictional-domain rules and rate limits. No real email is sent.

Files: `templates/components/header.html`, `footer.html`, `newsletter.html`, `nav_links.html`, new
`search_drawer.html`/`search_recommendations.html`, `templates/base.html`, homepage/copy templates,
`assets/css/app.css`, `static/js/navigation.js`, affected checks and this documentation.

## Executed checks

| Check | Actual result |
| --- | --- |
| Affected PostgreSQL tests | 68 passed in 6.99 seconds |
| Full PostgreSQL suite including isolated Admin browser test | **230 passed in 26.96 seconds** |
| Ruff lint / formatting | Passed |
| Django checks / migration drift | No issues / no changes detected |
| Tailwind / hashed static build | Passed |
| Homepage, catalog/detail/collections, bag and checkout | Chromium passed at 1440/1024/768/390/320px |
| Open navigation and search dialogs | Keyboard cycling, focus restoration, real images, search results and zero axe violations at all five widths |
| Header geometry | Centered wordmark and no utility overlap at all five widths |
| JavaScript disabled | Native menu and search link reach working server-rendered pages; shopping journey passes |
| Runtime / accessibility scans | No horizontal overflow, unexpected HTTP, application CSP or JavaScript errors; zero reported axe violations on checked states |

Chromium 156.0.8078.4, Playwright 1.64.0 and axe Playwright 4.13.0 were used. Existing tools stay outside
application dependencies. Reports and desktop/mobile screenshots are in ignored
`.qa/screenshot-refinement/chromium/`. Footer, navigation and search screenshots were visually reviewed.

QA was adjusted for native-dialog asynchronous close events and scoped searchbox selection where a
launcher/dialog/input share a name. Explicit focus cycling prevents Chromium's native Tab sequence
from moving briefly to browser chrome. Checkout input checks now inspect the checkout main landmark,
and newsletter checks identify its form by action because a global GET search form also exists.
The dedicated tests exercise open drawers; ordinary page audits still inspect visible content.

These local checks do not certify WCAG compliance. Safari/iOS, physical assistive technology and new
Lighthouse measurements were not performed for this revision. No deployment, push or commit occurred.

## Review and reproduce

Review `/` at `http://127.0.0.1:8000/`, use the menu and search icons, then scroll to the footer.
Search for “coat”; submit the newsletter only with a reserved address such as `guest@example.com`.
The existing demo rate limits apply when repeating submissions.

```bash
npm run css:build
uv run --locked --env-file .env manage.py runserver 127.0.0.1:8000
MAISON_BROWSER_QA=1 PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  uv run --locked --env-file .env pytest
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_drawers.mjs
MAISON_QA_OUTPUT=.qa/screenshot-refinement/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_homepage.mjs
MAISON_QA_OUTPUT=.qa/screenshot-refinement/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_catalog.mjs
MAISON_QA_OUTPUT=.qa/screenshot-refinement/chromium \
  PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers node scripts/qa_shopping.mjs
```
