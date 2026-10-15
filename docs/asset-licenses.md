# Asset provenance

Phase 3 includes eight generated editorial assets, self-hosted OFL fonts and a hand-drawn SVG
favicon. No reference-site photography, logos or Pinterest photographs were imported.

Before adding images or fonts, record each asset below. Pinterest is a moodboard source, not a
license to redistribute an image. Review authorization, applicable attribution and the rights needed
for public portfolio hosting. Keep product photography visually coherent.

| Local asset | Original source | License / authorization | Attribution | Notes |
| --- | --- | --- | --- | --- |
| `assets/editorial/sources/hero.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Landscape campaign |
| `assets/editorial/sources/women.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Women's editorial portrait |
| `assets/editorial/sources/men.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Men's editorial portrait |
| `assets/editorial/sources/coat.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Fictional charcoal coat |
| `assets/editorial/sources/knit.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Fictional ivory knit |
| `assets/editorial/sources/trousers.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Fictional sand trousers |
| `assets/editorial/sources/bag.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Fictional black tote |
| `assets/editorial/sources/atelier.webp` | Built-in imagegen | Generated for this fictional project | Provenance below | Imagined atelier scene |
| `static/fonts/inter-latin.woff2` | Google Fonts, Inter | SIL OFL 1.1 | `static/fonts/inter-OFL.txt` | Latin variable font |
| `static/fonts/cormorant-garamond-latin.woff2` | Google Fonts, Cormorant Garamond | SIL OFL 1.1 | `static/fonts/cormorant-garamond-OFL.txt` | Latin normal face |
| `static/fonts/cormorant-garamond-italic-latin.woff2` | Google Fonts, Cormorant Garamond | SIL OFL 1.1 | `static/fonts/cormorant-garamond-italic-OFL.txt` | Latin italic face |
| `static/images/favicon.svg` | Project-authored vector paths | Original project asset | Not applicable | Letter É monogram |

Font license sources:

- [Inter OFL](https://github.com/google/fonts/blob/main/ofl/inter/OFL.txt)
- [Cormorant Garamond OFL](https://github.com/google/fonts/blob/main/ofl/cormorantgaramond/OFL.txt)

Full generation prompts, dates, mode and master paths are recorded in
[`assets/editorial/provenance.json`](../assets/editorial/provenance.json). No reference images were
supplied to the generator. These visuals illustrate fictional garments, models and an atelier;
they are not evidence of actual products or manufacturing. No claim of exclusive copyright is made.

The selected outputs were saved as high-quality WebP masters in the workspace. Responsive derivatives
are versioned under `static/images/editorial/`; `assets/editorial/image-manifest.json` records dimensions
and sizes. Nineteen derivatives total approximately 1.4 MiB; the desktop hero's 1600px version is
176,640 bytes and its mobile 800px version 78,690 bytes. These are file sizes, not page-load benchmarks.

`scripts/build_editorial_images.py` reproduces the derivatives from the masters using Pillow 12.3.0.
Processing converts to RGB, strips metadata, scales images and crops the mobile hero; it does not
alter subjects or scenes. Font download URLs and SHA-256 checksums are in `static/fonts/font-manifest.json`.
Assets are served locally, without visitor requests to Google Fonts or the generation service.

Product media is now managed through catalog models/admin. The Phase 4 seed command uses the approved
coat, knit, trousers and bag masters to generate sanitized responsive files in local media storage.
Phase 6 added 320/720px editorial sizes and a 640px mobile hero, using WebP quality 78 while preserving
masters. The current manifest records 34 derivatives totaling about 1.63 MiB; Phase 3's original
nineteen-file sizes above are historical measurements. Image markup now reads actual dimensions from
that manifest. No external brand photographs were introduced. Uploaded runtime media remains
ignored. Approved seed assets and their attribution will retain a deliberate versioned location.

## Owner-requested catalog expansion — 2026-10-14

Ten additional original photographs were generated through the built-in imagegen tool. No Dior
photographs, logos or source code were used. All ten final WebP masters live under
`assets/editorial/sources/`; their complete prompts, dates and generation mode are recorded in
`assets/editorial/provenance.json` alongside the original eight assets.

| Master filename | Fictional product |
| --- | --- |
| `overshirt.webp` | Chocolate wool overshirt |
| `linen-shirt.webp` | Ivory linen shirt |
| `tailored-blazer.webp` | Taupe tailored blazer |
| `merino-cardigan.webp` | Oatmeal merino cardigan |
| `silk-dress.webp` | Black silk midi dress |
| `navy-trousers.webp` | Navy straight wool trousers |
| `zip-jacket.webp` | Olive twill blouson |
| `pleated-skirt.webp` | Slate pleated midi skirt |
| `merino-top.webp` | Burgundy merino turtleneck |
| `wool-scarf.webp` | Camel brushed wool scarf |

Generated outputs were converted to high-quality WebP masters (quality 94) without scene changes.
The derivative manifest now contains 74 files, totaling 2,610,260 bytes (about 2.49 MiB) across all
eighteen masters and the mobile hero crop. This is the complete asset library, not a page download.
The expanded seed copies the ten new product images into the same validated, metadata-free,
UUID-named managed media pipeline. Runtime uploads remain ignored.

Navigation/footer/filter icons are project-authored SVG paths in `templates/components/icon.html`.
They share one outline style and do not introduce an icon dependency or copied brand assets.

## Campaign storefront revision — 2026-10-15

- `assets/editorial/sources/coastal-campaign.webp` is an original built-in imagegen photograph of
  fictional adult models in a coastal architectural setting. The complete prompt, generation mode,
  date and selected master path are in `assets/editorial/provenance.json`. It uses no reference-site
  photographs and makes no claim of a real location, person, product or endorsement. Existing masters
  were preserved. Pillow converted the selected output to a quality-94 WebP master and produced six
  metadata-free desktop/mobile derivatives; the mobile crop centers both models.
- `static/fonts/jost-latin.woff2` is the Google Fonts Latin variable subset of Jost, licensed under
  SIL OFL 1.1. The authors' notice is retained in `static/fonts/jost-OFL.txt`. Source URLs, 26,576-byte
  size and SHA-256 are recorded in `static/fonts/font-manifest.json`. Jost and the existing Cormorant
  wordmark are original font choices for this project, not a claim about Dior's actual typefaces.
  [Official license](https://github.com/google/fonts/blob/main/ofl/jost/OFL.txt).

The current library has nineteen generated masters and 80 derivatives totaling 2,927,334 bytes
(about 2.79 MiB). The new desktop 1600px campaign is 103,592 bytes; its 800px mobile crop is 45,172
bytes. These are recorded file sizes, not new performance benchmarks. All visitor font/image requests
remain local to the site. No Dior logo, custom font file, photograph or source bundle is shipped.
