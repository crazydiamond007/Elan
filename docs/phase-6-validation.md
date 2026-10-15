# Phase 6 validation and handoff

Executed on 2026-10-14 (Europe/Istanbul) in WSL Ubuntu. This phase completes local polish, audits,
security review and concrete deployment preparation. It does not publish or activate a hosted service.

## Delivered

- Catalog heading hierarchy, accurate responsive image dimensions, additional WebP sizes, mobile
  input sizing and progressive form error/pending feedback. Original image masters are preserved.
- Accessible Admin breadcrumbs/filter targets, labelled variant/date/time controls, native collection
  checkboxes and native publication inputs. Actual editing/upload/logout is browser-tested.
- Open Graph metadata, escaped nonce-bearing WebSite/Product JSON-LD, and an XML sitemap using only
  public records and the configured canonical origin. Private/error pages omit share metadata.
  The demo remains no-index; fictional Product metadata includes no offers or fabricated ratings.
- Shared admin-login throttling, trusted-proxy client-address validation and serialized established
  shopping-session writes. Existing parallel cart changes no longer overwrite each other.
- Dynamic HTML gzip with Django's randomized padding, private HTML caching, immutable asset policy,
  and a non-debug loopback review profile for reproducible local measurements.
- Gunicorn 26.2.0 runtime, digest-pinned multi-stage Docker build, restricted Compose web service,
  separate-media configuration, Nginx example, liveness/readiness endpoints and deployment handoff.
- Python/frontend dependency auditing and documentation of actual checks versus hosting-dependent work.

## Executed verification

| Check | Actual result |
| --- | --- |
| Full PostgreSQL pytest suite including optional Admin browser test | **228 passed in 24.09 seconds** |
| Ruff lint / formatting | Passed; final handoff check confirmed 112 Python files formatted |
| Django checks / migration drift | No issues / no changes detected; no Phase 6 schema migration |
| uv dependency consistency | Sixteen installed packages compatible |
| Python advisory audit, pip-audit 2.10.1 | No known vulnerabilities reported for the locked set |
| npm audit | Zero reported vulnerabilities for the application lockfile |
| Tailwind CSS build | Passed; generated CSS 30,424 bytes at the recorded build |
| Production static build | 173 source assets in the clean image; 445 post-processed outputs |
| Docker build | Passed with pinned Python/Node/uv digests and locked dependencies |
| Restricted container smoke | Passed: non-root, read-only root, dropped capabilities, no network/host mounts |
| Compose schema | Validated without resolving a nonexistent real production environment file |
| Nginx example | Parse check passed with Nginx 1.30.5 and temporary QA certificates |
| Production deployment checks, HSTS=0 | Expected W004; none silenced |
| Production deployment checks, explicit HSTS=300 | Expected W005/W021 for intentionally disabled subdomain/preload commitments |

Gunicorn is the one new application dependency; the locked 26.2.0 release supports the existing
Python 3.13 runtime. Lighthouse/browser tools stay outside project dependencies. Package scans do
not establish absence of vulnerabilities in code, operating-system packages or embedded native libraries.
Scan the final release image and refresh advisory data before public activation.

On resuming the interrupted handoff, Ruff and the Lighthouse/Admin script syntax checks passed
again. Docker Desktop's CLI integration was unavailable in this WSL distro, so the final container
smoke could not be repeated. The Docker results above record the earlier successful checks;
repeat the release-image smoke once Docker integration is restored, before deployment.

Concurrency tests verify shared rate-counter enforcement, duplicate receipt idempotency and parallel
cart additions preserving both changes. Security tests cover proxy spoofing, invalid configuration,
admin limits, CSRF, session isolation, safe errors, metadata escaping and published-only sitemap data.
Query bounds remain explicit: catalog seven; detail first visit ten including session creation,
returning detail seven; homepage six; cart snapshot two. Generic 500/liveness rendering uses no SQL.

## Browser and accessibility review

Chromium 156.0.8078.4 and Firefox 157.0 used Playwright 1.64.0 and axe Playwright 4.13.0. Both engines
passed homepage, catalog/detail/collections, empty/populated bag and checkout at widths 1440, 1024,
768, 390 and 320 pixels. Selected WCAG 2.x A/AA scans reported zero violations after fixes; normal
journeys had no unexpected HTTP, JavaScript or application CSP errors or external-origin asset requests.
Screenshots were inspected, including Firefox's mobile homepage and the revised mobile checkout.

Both engines completed search/filter/sort → product → add/update/remove → sale item → simulated
checkout → private confirmation → empty bag with JavaScript disabled. Another session received 404
for the confirmation URL. Reserved-address newsletter success and rejected genuine-domain input
were exercised with local demo data. Error states, skip link, menu keyboard/Escape focus, outside
dismissal, reduced motion and local asset loading were also checked.

The isolated Admin browser test uses pytest's disposable PostgreSQL database and a test-only
administrator, never the development user database. Login, product editing, inline stock editing,
image replacement and POST logout passed. Dashboard, catalog list and product change screens reported
zero axe violations. axe's own inline layout probes initially triggered CSP warnings; the QA harness
now gives only those audit-created style elements the existing response nonce, then restores the DOM
factory. Application CSP is unchanged, and application interactions are checked independently.

Automated scores and scans are not WCAG certification. Physical screen-reader testing, Safari/iOS
and chosen-host cookie/TLS behavior remain acceptance checks before public exposure.

## Lighthouse measurements

Lighthouse 13.5.0 measured the final local non-debug Gunicorn server at `127.0.0.1:8001`, with hashed/
compressed static assets, immutable local review media and no real TLS/CDN/provider. Each table row
is one complete lab run; numbers vary with machine load and do not represent field-user performance.
Mobile configuration: 412×823, DPR 1.75, fourfold CPU slowdown and simulated slow 4G. Desktop uses
Lighthouse's explicit desktop configuration at 1350px. Reports assert the actual form factor matches
their label. All final measurements recorded zero total blocking time and zero layout shift.

| Page | Mode | Performance | Accessibility | Best practices | SEO | LCP |
| --- | --- | --- | --- | --- | --- | --- |
| Home | Mobile | **97** | 100 | 100 | 69 | 2.49 s |
| Home | Desktop | **100** | 100 | 100 | 69 | 0.69 s |
| Catalog | Mobile | **100** | 100 | 100 | 69 | 1.88 s |
| Catalog | Desktop | **100** | 100 | 100 | 69 | 0.48 s |
| Coat detail | Mobile | **98** | 100 | 100 | 69 | 2.33 s |
| Coat detail | Desktop | **100** | 100 | 100 | 69 | 0.50 s |

SEO is 69 because the demo deliberately blocks indexing. Do not remove no-index/robots protections
to improve that score. Other reported opportunities include image delivery/render blocking and
above-fold catalog image discovery. Large further image changes were not made at the expense of
the approved art direction. The initial valid mobile baseline was 95 on the development server;
server mode/compression/cache policies also changed, so it is not a controlled attribution experiment.

An earlier Node API `preset` flag was ignored and mislabeled a second mobile run as desktop. Inspection
of `configSettings` caught it; explicit desktop configuration and a form-factor assertion replaced
that approach. Earlier desktop-labelled scores are discarded. Final reports above reflect the verified
configuration. Lighthouse inherited Windows LOCALAPPDATA and created repository-local audit profiles;
those generated artifacts were moved into ignored QA storage without deleting files. New profiles
are explicitly created under `/tmp` through a native Chromium process. The launcher's WSL path
translation also produced UNC-named directories during the first correction; these were preserved
in ignored QA storage too. A runner smoke confirmed zero repository profile directories, and the
final image excludes both forms of generated artifact.

## Reproduce

README describes the local Gunicorn review profile and build. Optional tools live under `/tmp`:

```bash
npm install --prefix /tmp/maison-elan-browser --no-package-lock --ignore-scripts \
  playwright@1.64.0 @axe-core/playwright@4.13.0 lighthouse@13.5.0 prettier@3.9.10
PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  /tmp/maison-elan-browser/node_modules/.bin/playwright install chromium firefox
MAISON_BASE_URL=http://127.0.0.1:8001 PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  node scripts/qa_homepage.mjs
MAISON_BASE_URL=http://127.0.0.1:8001 PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  node scripts/qa_catalog.mjs
MAISON_BASE_URL=http://127.0.0.1:8001 PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  node scripts/qa_shopping.mjs
MAISON_BASE_URL=http://127.0.0.1:8001 PLAYWRIGHT_BROWSERS_PATH=/tmp/maison-elan-browser/browsers \
  node scripts/qa_lighthouse.mjs
MAISON_BROWSER_QA=1 uv run --locked --env-file .env pytest
```

Set `MAISON_BROWSER=firefox` for the three page/journey scripts to repeat them in Firefox. Their
artifacts use `.qa/phase-6/chromium/` and `firefox/`; Admin and Lighthouse have separate report folders.
QA obeys actual abuse limits; repeated newsletter/checkout runs in one window can return 429.
The published Lighthouse-script assertion prevents accidental form-factor misreporting.

To refresh package auditing without adding a project tool dependency:

```bash
uv export --locked --format requirements-txt --no-emit-project \
  --output-file /tmp/maison-elan-requirements.txt --quiet
uvx --from pip-audit==2.10.1 pip-audit --require-hashes --disable-pip \
  -r /tmp/maison-elan-requirements.txt
npm audit
```

## Production handoff

[Deployment instructions](deployment.md) describe the concrete image, Compose/runtime, proxy, separate
media hostname, CA mounting, migrations, backup/retention and maintenance scheduling. The Docker smoke
validated boot and database-free pages/assets with dummy configuration, no network and a forwarded
HTTPS header. The proxy parser used disposable self-signed QA certificates. Neither proves real
hosted HTTPS, certificate renewal, PostgreSQL TLS/connectivity, media persistence or backup restore.

HSTS remains deferred until real TLS verification; includeSubDomains/preload are intentionally off.
Configure exact trusted proxy peers, least-privilege database roles, scheduler, domain/certificates,
media mount/storage and infrastructure abuse controls on the selected host. Physical accessibility
acceptance and final image/native-library advisories also belong to that release review.
No source was committed/pushed, no secrets were printed, and nothing was publicly deployed.
