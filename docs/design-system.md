# Design direction

**Latest pagination/title refinement, 2026-10-16:** [numbered pagination and page titles](numbered-pagination-validation.md)
documents the owner-requested outlined panel, Previous/Next pills, active numbered circles and
separate page status. Browser and social title separators now use a vertical bar rather than an em dash.

**Latest refinement — 2026-10-15:** the [flagship design review](flagship-design-review.md)
adds a two-level typographic signature, a four-view coat gallery, enhanced colour/size selection
and Admin-curated companion products. The established palette, homepage photography, drawers
and footer remain the foundation. Earlier notes describe their respective implementation dates.

**Current header/footer — 2026-10-15:** the owner's supplied screenshots guide the focused
[header, drawer and footer refinement](header-footer-validation.md). The restored warm homepage,
typography and fourteen-product catalog remain, with a single-row white header, menu/search drawers,
serif footer columns and footer newsletter. The “The maison” copy and large footer wordmark are
removed. The restoration note below records the preceding step, before this focused refinement.

**Current status — 2026-10-15:** the owner rejected the later Dior-reference redesign. The preceding warm ivory design documented below and in `design-refinement-validation.md` is restored, including Inter typography, the original terrace hero, static desktop navigation and expanded footer. The fourteen-product catalog is preserved. The rejected `storefront.css` is not imported; its campaign image and Jost files remain unused in the workspace.

Phase 3 implements a modern, minimal, premium editorial direction: warm limestone photography,
charcoal tailoring, generous whitespace and a restrained Autumn / Winter 26 campaign.

| Token | Value | Intended use |
| --- | --- | --- |
| Ivory | `#F7F5F0` | Primary background |
| Off-white | `#FAF9F6` | Supporting surfaces |
| Charcoal | `#222222` | Text, focus indicators and primary controls |
| Warm grey | `#A7A29A` | Supporting accents; not assumed suitable for body text |
| Taupe | `#C6B8A8` | Decorative borders and supporting surfaces |
| Muted text | `#64625D` | Secondary readable text |
| Stone | `#EEE9E1` | Campaign and newsletter surfaces |
| Line | `#D6D1C7` | Decorative dividers |

Calculated solid-color contrast ratios: charcoal/ivory **14.60:1**, muted/ivory **5.59:1**,
muted/stone **5.04:1**, off-white/charcoal **15.11:1**, and charcoal/stone **13.17:1**.
These calculations do not certify contrast over every photograph. The hero uses dark text over
a light, uncluttered stone area with a subtle overlay; its mobile text moves below the photograph.

The shell includes a skip link, semantic landmarks, visible focus and targets at least 44px high.
The menu is a native disclosure with JavaScript dismissal/focus enhancements. Links work without
JavaScript. Motion is limited to hover feedback and smooth scrolling, both disabled for reduced motion.

Inter supplies interface text; Cormorant Garamond supplies editorial headlines, including a genuine
italic face. Latin WOFF2 subsets are self-hosted with `font-display: swap`. Only the two primary
normal faces are preloaded. OFL notices, source URLs and checksums are retained in `static/fonts/`.

The homepage includes an announcement bar, navigation, art-directed hero, three category tiles,
new arrivals, seasonal campaign, curated signature edit, atelier story, newsletter presentation and
comprehensive footer. Calls to action now lead to database-backed catalog/detail pages, information
pages or existing sections. Legacy preview URLs redirect to their catalog equivalents.
Products and prices are clearly fictional; the best-seller preview is curated and reports no sales.
Newsletter signup is visibly disabled and collects no input until its implementation phase.

Desktop uses a 1680px maximum content shell, responsive 20–72px gutters and 64–128px section spacing.
Product cards use a 3:4 image ratio and categories a 4:5 ratio. Tablet/mobile layouts reduce columns,
stack editorial sections and use a separate hero crop that keeps both models visible.

Reference research retrieved navigation/page content from TOTEME, COS and Aritzia. It did not
verify visual layout, responsive behavior, hover interactions or photography composition in a browser.
Do not copy their assets, trademarks or complete layouts. The UI/UX skill supplied general
accessibility guidance; its suggested glass styling was rejected in favor of the owner's brief.

Tailwind 4 targets Chrome 111+, Safari 16.4+ and Firefox 128+. Use literal complete utility classes
in templates. `assets/css/app.css` explicitly scans templates, applications and local JavaScript.
Component styles live in Tailwind's component layer and use the shared color/type/spacing tokens.
No animation framework, Alpine.js, frontend bundler or runtime icon library was introduced.

Phase 4 extends the system with restrained catalog navigation, spacious product grids, native
variant-selection forms, a responsive product gallery and disclosure panels. Selection is explicit
and works without JavaScript. Missing photographs, empty collections, unavailable sizes and form
errors have honest, visible states. At the Phase 4 boundary the bag button was visibly disabled.

Phase 5 adds a native filter disclosure, clear labels/errors, bag editing, a restrained summary panel
and a simulated checkout. Product forms support previewing options and directly adding the submitted
selection. Mobile checkout puts the summary before confirmation; desktop uses two columns. Buttons
describe demo actions explicitly. The newsletter labels fictional input and local storage. Standard
page navigation and status feedback handle submissions without introducing asynchronous JS or a
frontend framework. The existing palette, fonts and reduced-motion behavior are retained.

See `docs/phase-3-validation.md`, `docs/phase-4-validation.md` and `docs/phase-5-validation.md`
for executed browser checks and limits.

Phase 6 corrects catalog card heading levels, supplies accurate image dimensions, increases Admin
filter targets, labels date/variant controls, and replaces problematic multi-select presentation with
native collection checkboxes. New mobile product inputs use 16px text. An external form script focuses
error summaries, marks pending submissions and restores controls on browser history navigation;
native forms continue to work without it. Chromium and Firefox screenshots/audits are recorded in
`phase-6-validation.md`; automated scores are evidence for tested scenarios, not certification.

The owner-requested refinement after Phase 6 uses a centered editorial-serif wordmark, a separate
desktop navigation row and original 24px outline SVGs with a consistent 1.35px stroke. Search and
bag icons have descriptive accessible names and 44px targets. On narrow 320px screens, search remains
available through the native menu. The header stays in normal flow so it does not obscure content.

The footer adds three useful guidance links, a newsletter destination and four clear navigation
groups. Product cards use a consistent name/color/price stack; the listing integrates its count with
the native filter disclosure. An original full-width editorial interlude appears after eight cards
when an unfiltered first page has at least eight products. Filtered and paginated results retain a
continuous shopping grid. Ten new original product photographs keep the warm studio art direction.
See `design-refinement-validation.md` for the separate review evidence.
