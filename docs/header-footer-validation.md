# Screenshot-led header, drawers and footer — 2026-10-15

## Screenshot-aligned search correction — 2026-10-18

The owner rejected the compact side-by-side card and supplied a clearer Dior reference: an edge-aligned
right panel with the search field, suggestions and recommendation row stacked along the same left edge.
The current design follows that arrangement. The panel occupies approximately half a large desktop
viewport and an inset phone viewport. A follow-up restores the reference's visible box edges: **8px
rounded corners** with a **16px outer gap** on desktop, **12px** on phones and **8px** on short screens.
Three product previews, including their names, remain visible. Short-screen spacing is tightened to
preserve that visibility after adding the outer gap.
Image heights, toolbar spacing and section margins adapt to viewport height. Two-column suggestions
save vertical space on phones and short screens; recommendations stay below them.

Diagnosis reproduced overflow in the prior layout at 560×420, 480×360 and 430×400. These sizes are
now included in the browser checks. The stylesheet URL also receives a stable modification-time
version in development, changing after each CSS rebuild; non-debug deployments retain the configured
static storage's manifest URLs. This prevents a previous cached development stylesheet from surviving
a normal refresh. Cached CSS was a possible contributing factor, not a confirmed cause on the owner's
browser.

Executed validation for the correction:

- **33 affected Python tests passed in 2.31s**, including stylesheet-version refresh behavior and
  existing public-page/editorial behavior.
- Chromium passed at **16 viewport sizes**, including the supplied screenshot's **1912×840**, the
  earlier eleven sizes, and **560×420, 480×360, 430×400 and 320×480**. Search requires no scrolling
  in those tested states; bounds checks include every recommendation link and its product name.
  Additional checks require vertical stacking and a common left edge for all three sections.
  The follow-up also checks a positive outer gap and an 8px corner radius at every size; desktop
  captures were visually reviewed to confirm the rounded inset panel.
- Navigation/search keyboard focus, close/focus restoration, image loading and real search submission
  passed; audited dialogs reported zero axe A/AA violations or browser errors. Fifteen contextual
  layout checks and constrained 320×256px keyboard reflow still pass, as does the no-JavaScript fallback.
- The 1912×840 desktop and 390×844 phone screenshots were visually reviewed against the owner's
  supplied arrangement. Reports/captures remain in ignored `.qa/search-panel/chromium/`.
- Tailwind, production hashed static collection, Ruff, formatting, JavaScript syntax and
  `git diff --check` passed. No dependency was added. Extremely constrained viewports retain scrolling
  so content stays reachable rather than being clipped.

## Earlier compact card trial — superseded

The owner requested that the search field, suggestions and recommended products be visible without
scrolling. Search now has its own content-sized height, an 860px maximum width, a shorter toolbar
and tighter spacing. Setting `bottom: auto` prevents the native dialog's default inset from stretching
the panel into unused space. Desktop places suggestions beside product previews; phones use a two-column
suggestion list above smaller previews. Short landscape viewports use reduced vertical spacing.
Product names remain visible, inputs retain 16px text, and controls retain at least 44px targets.
The shared navigation drawer, existing form behavior and native modal handling remain intact.

Executed checks using `scripts/qa_drawers.mjs` and Chromium 156.0.8078.4:

- All search content fits with no internal scrolling at **1920×1080, 1440×900, 1366×768, 1280×600,
  1024×768, 768×1024, 390×844, 375×667, 320×568, 844×390 and 667×375**. Geometry checks verify
  every search destination is in the panel, the panel stays within the viewport, and it ends within
  25px of its content. Desktop, small-phone and landscape screenshots were visually reviewed.
- Navigation/search focus containment, close/focus restoration, real image loading and search
  submission passed, with no reported axe A/AA violations or browser errors at those eleven sizes.
- Fifteen further layout checks cover related-product previews and category fallback content on
  product, story and empty-search pages at desktop, laptop, small-phone and landscape sizes.
- At a constrained **320×256px** reflow viewport, internal scrolling remains available and keyboard
  navigation reaches the last preview; Escape closes the dialog. Content is never hidden to force
  a fit. The no-JavaScript navigation/search fallback also passed.
- Tailwind compilation, JavaScript syntax/format checks, Ruff, production hashed static collection
  and `git diff --check` passed. No backend, dependency or database change was needed.

Reports and screenshots: ignored `.qa/search-panel/chromium/`. These are local Chromium checks,
not physical-device or assistive-technology certification. Earlier full-height search styling and
the old QA output directory below are historical; the menu drawer still uses its original height.

## Original implementation

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
