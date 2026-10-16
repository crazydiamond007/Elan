# Catalog image and pagination correction — 2026-10-16

The later [numbered pagination refinement](numbered-pagination-validation.md) supersedes the
three-column pagination layout described below. The landscape image correction remains current.

The owner identified a head-cropping issue in the catalog editorial panel and vertically misaligned
pagination text. This focused correction preserves the rest of the storefront and existing local work.

## Changes

- Replace the reused portrait in the catalog interlude with an original landscape photograph.
  The fictional model is shown full-length beside a limestone bench, wearing chocolate wool,
  an ivory knit and sand tailoring. The original category photograph remains in its existing uses.
- Give the image frame a 3:2 aspect ratio, a desktop minimum height and alignment with the text
  column. Mobile uses a square frame. Its geometry preserves the image's full height at all checked
  widths, including the 1920px case where a fixed shallow frame would still trim the new photograph.
- Provide responsive 480/800/1200/1536px WebP derivatives. The sizes hint accounts for the extra
  source width needed when covering a square/narrow frame with a landscape image.
- Use three pagination columns with a centered page count. Links and the page count share 44px
  minimum heights, line height and vertical centering. Empty previous/next slots retain the layout
  at the first and last pages. Existing query strings and server-side pagination are unchanged.

## Asset provenance

The built-in imagegen tool generated the photograph without reference images. Pillow saved a
metadata-free quality-94 master at `assets/editorial/sources/catalog-interlude.webp`; responsive
copies use quality 78. The full prompt and generation mode are recorded in
[catalog interlude provenance](../assets/editorial/catalog-interlude-provenance.json).
No reference-brand asset was used. This image depicts fictional garments and a fictional adult model.

## Executed checks

- Affected PostgreSQL tests: **70 passed in 8.35 seconds** (editorial, catalog and search modules).
- Browser audit at **1920, 1440, 1024, 768, 390 and 320px**: image loaded, full-height frame geometry,
  both first/last page controls vertically aligned, page count centered, targets at least 44px high,
  no horizontal overflow, no browser errors and zero reported axe violations.
- The desktop and mobile editorial panel and first/last pagination captures were visually reviewed.
- Ruff, Python formatting, CSS formatting, Tailwind compilation and `git diff --check` passed.
- Production hashed static collection passed with the new responsive assets and stylesheet.

The focused browser script is temporary QA tooling at `/tmp/maison-catalog-review.mjs`; its report
and screenshots are in ignored `.qa/catalog-panel-fix/`. No application dependency, migration,
catalog inventory, commit, push or deployment was added by this correction.

Review at `http://127.0.0.1:8000/shop/`, then follow Next page and Previous page.
