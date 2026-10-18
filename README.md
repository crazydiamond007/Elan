# MAISON ÉLAN

A fictional premium fashion label and demonstration shopping experience, built as a
server-rendered Django monolith. No real payments, customer orders or fulfilment.

Phases 1–6 deliver the editorial storefront, managed catalog, search/filtering, a session shopping bag,
simulated checkout and fictional newsletter signup. Phase 6 adds metadata/sitemap support, measured
browser audits, admin login protection, concurrent shopping-session updates and production artifacts.
All products, prices and delivery remain fictional. Public hosting still needs deployment approval
and verification of real HTTPS, database/media infrastructure and operations.

## Requirements

- WSL2 Ubuntu; keep the repository on the Linux filesystem.
- uv 0.11.28 or a compatible current release.
- Python 3.13.14 (recorded in `.python-version`).
- Node 24 / npm 11 (`.nvmrc` records the verified Node version).
- PostgreSQL 18, running locally with access to a PostgreSQL administrator for initial setup.

Open this directory with VS Code's WSL integration. Select `.venv/bin/python` as the interpreter.

## First-time setup

```bash
uv sync --locked
npm ci --ignore-scripts
uv run --locked python scripts/create_local_env.py
```

The environment helper creates `.env` with random secrets and mode `0600`. It refuses to
replace an existing file and never prints the secrets. `.env.example` documents the variables.
Do not commit `.env`, credentials, uploaded media, or database exports.

Check PostgreSQL before provisioning:

```bash
pg_lsclusters
pg_isready -h 127.0.0.1 -p 5432
```

If your WSL account is a local PostgreSQL administrator via peer authentication:

```bash
uv run --locked --env-file .env python scripts/provision_local_db.py
```

This creates the dedicated `maison_elan` role and database. The role can create test databases,
but cannot administer roles or act as a superuser. Existing roles and databases are preserved.
The helper uses safe SQL identifiers/literals and does not put passwords in command arguments.
It is a local development helper, unsuitable for production provisioning.

If peer authentication does not provide administrative access, provision the role/database
through your PostgreSQL administrator. From `sudo -u postgres psql`, for a new installation:

```sql
CREATE ROLE maison_elan LOGIN CREATEDB NOSUPERUSER NOCREATEROLE NOREPLICATION;
\password maison_elan
CREATE DATABASE maison_elan OWNER maison_elan ENCODING 'UTF8' TEMPLATE template0;
```

Set the same database password in your private `.env`. Preserve any existing database objects;
do not repeat these statements blindly. No helper starts, reconfigures or replaces a cluster.

```bash
uv run --locked --env-file .env manage.py migrate
uv run --locked --env-file .env manage.py seed_catalog
npm run css:build
```

An environment has already been created and migrations applied in the initial workspace.
On this workspace, preserve `.env` and skip its creation/provisioning unless setting up anew.

## Development

In one WSL terminal:

```bash
uv run --locked --env-file .env manage.py runserver 127.0.0.1:8000
```

In a second terminal:

```bash
npm run css:watch
```

Run one CSS watcher per checkout. Stop existing watchers before switching build processes so an
older process cannot overwrite the current stylesheet.

Visit <http://127.0.0.1:8000/>. The demo information is at `/demo/` and admin login at `/admin/`.
Use loopback binding for local development; Django's development server is not a deployment server.

Create your administrator interactively, choosing your own password:

```bash
uv run --locked --env-file .env manage.py createsuperuser
```

No administrator or default password is seeded. Django's password validators remain enabled.

Browse `/shop/`, `/collections/` and `/products/sculpted-coat/`. Open **Search, filter & sort** to search
by name/description/SKU and filter by category, price, size and colour. On a product page, select
options and **Add to demo bag**, or choose **Update selection** to preview availability first.
Size L is unavailable in the seeded clothing data; the trousers demonstrate sale pricing.

At `/bag/`, update quantities or remove items. **Continue to demo checkout** shows fixed fictional
details and requires explicit acknowledgement. Completion creates a simulated confirmation, empties
the bag and leaves catalog stock untouched. No payment or real delivery information is collected.
Confirmation links work only in the browser session that completed checkout. The whole journey works
with JavaScript disabled.

The homepage and `/newsletter/` accept fictional reserved addresses such as `guest@example.com`.
They store demo signups locally, send no email, reject real addresses and handle duplicates safely.
Demo signups and receipts remain in the local database until removed by the owner through Admin.

Shopping and newsletter POST endpoints use CSRF protection and shared PostgreSQL rate limits.
Counters expire and need a scheduled maintenance command on deployment:

```bash
uv run --locked --env-file .env manage.py prune_rate_limits
```

This removes expired counters only. Django's standard `clearsessions` command handles expired sessions.
Phase 6 serializes changes to an established shopping session, including middleware persistence;
concurrent additions and duplicate checkout are tested on PostgreSQL. Product pages establish the
shopping cookie before submission. Verify real-host behavior and trusted-proxy addresses before launch.

`seed_catalog` creates four fictional products, thirteen variants, two categories and two collections.
It uses the versioned original image masters and copies sanitized responsive files to local media.
Existing product records, prices, stock, images and editorial edits are left untouched on reruns.
It does not repair incomplete existing products. Changes made through Admin appear in storefront
queries; a product needs an active category, an active variant and a reached publication date.

The approved design refinement adds ten original product photographs and an optional catalog
expansion (fourteen products and fifty variants in a fresh database):

```bash
uv run --locked --env-file .env manage.py seed_catalog --extended
```

This uses the same preservation rules and does not reset existing Admin edits. The development
database has already received this expansion. See [design refinement validation](docs/design-refinement-validation.md)
for its scope, asset provenance and executed checks.

The later Dior-reference redesign was withdrawn at the owner's request on 2026-10-15. The prior
warm ivory design, Inter typography, original terrace hero, navigation and footer are restored;
the expanded fourteen-product catalog remains. Its unused campaign/font/style assets and historical
report are preserved, but the rejected stylesheet is no longer imported.

The owner's subsequent screenshots guide the current [header/footer refinement](docs/header-footer-validation.md):
single-row navigation, separate menu/search drawers, a footer newsletter and serif link columns,
with the large footer wordmark removed. The restored homepage artwork and expanded catalog are retained.

The subsequent [flagship refinement](docs/flagship-design-review.md) introduces the compact ÉLAN
wordmark, a four-photograph coat gallery with enlargement, enhanced size/colour selection and
Admin-curated outfits. After migrations and the base catalog seed, add its optional gallery with:

```bash
uv run --locked --env-file .env manage.py seed_editorial
```

This preserves existing photographs, curation, prices and stock. Review `/products/sculpted-coat/`;
the subsequent [merchandising refinement](docs/merchandising-validation.md) adds image-led collections,
alternate product-card photographs, sale comparisons, a compact purchasing area, mobile footer
disclosures and detailed bag feedback. After the extended catalog and editorial seed, run:

```bash
uv run --locked --env-file .env manage.py seed_merchandising
```

This adds fifteen original photographs to five more signature products and fills missing collection
covers/outfit selections. It preserves occupied image positions, existing covers, curation, prices
and inventory. It refuses to guess if a signature product's front-photo colour has changed. The local
workspace has already received these assets. All six signature products now have front, styled,
back and detail views; the remaining products retain their existing photographs.

Choose **Catalog → Collections → Cover image** in Admin to set each collection's photograph.
Covers appear only while their source product is public. The first featured collection with a
public cover, ordered by position, also supplies the homepage campaign photograph and destination.
Collections without covers use a typographic placeholder. Card photo buttons support touch and
keyboard use; mobile footer groups expand natively. Without JavaScript, footer links remain visible
and every normal shopping destination/form remains available.

The bag icon counts quantities in the bounded session cart, including items that may subsequently
become unavailable until removed. Adding an item shows its selected product, colour, size and added
quantity after the server validates it. Bag feedback uses the existing server-rendered redirect flow.

## Checks

```bash
uv run --locked --env-file .env manage.py check
uv run --locked --env-file .env manage.py makemigrations --check --dry-run
uv run --locked --env-file .env pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv pip check
npm run css:build
npm audit
```

pytest explicitly selects `config.settings.test`, even when `.env` selects development settings.
Tests use PostgreSQL and create/drop `test_maison_elan`; never point test settings at production.
Use a dedicated database/role if running tests concurrently in multiple checkouts.

`npm ci --ignore-scripts` uses the locked, prebuilt Linux native packages without running
dependency lifecycle scripts. This workflow was verified on WSL x86-64. Other platforms may
require reviewing platform-specific native packages before changing that policy.

Tailwind and its CLI are pinned to 4.3.0 because 4.3.1–4.3.3 pin an affected watcher version.
The lockfile uses `@parcel/watcher` 2.6.0. Reassess the pin when upstream fixes that dependency.
See [Tailwind's package metadata](https://github.com/tailwindlabs/tailwindcss) and
[the braces advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm).

## Assets and configuration

- `assets/css/app.css`: Tailwind source, design tokens, typography and responsive components.
- `assets/editorial/`: versioned image masters, generated-image prompts and derivative manifest.
- `templates/`: shared components, editorial homepage, catalog/detail/information pages and safe errors.
- `static/`: versioned JavaScript, fonts and brand assets; generated CSS is ignored.
- `media/`: local uploads, ignored and served only under development settings.
- `staticfiles/`: ignored deployment build output from `collectstatic`.
- `config/settings/`: separate development, test and production settings.
- `apps/accounts/`: custom Django user and admin registration.
- `apps/core/`: homepage queries, seed-source capsule, legacy redirects, demo disclosure and errors.
- `apps/catalog/`: product/variant/image models, public querysets, selection forms, listings and admin.
- `apps/cart/`: bounded session cart, availability checks, totals, POST changes and bag presentation.
- `apps/checkout/`: reviewed demo snapshots, idempotent receipts and session-bound confirmations.
- `apps/marketing/`: reserved-address signup forms, local demo records and admin.
- `deploy/`, `Dockerfile`, `compose.production.yaml`: reviewed production build/proxy examples.

The original capsule in `apps/core/editorial.py` is retained only as seed input. Storefront prices,
images, inventory and visibility come from the database. Old `/collection-preview/` links redirect
to the catalog. Signature/best-seller placements are curated demo content, not fabricated sales data.

Responsive WebP assets and fonts are versioned and need no download to serve a fresh checkout.
To rebuild image derivatives from the versioned masters:

```bash
uv run --locked python scripts/build_editorial_images.py
```

The optional font download helper is for deliberate asset updates, not routine setup:
`uv run --locked python scripts/download_fonts.py`. It fetches licensed WOFF2 subsets and records
their exact sources and checksums. Review the resulting assets before committing changes.

Staff can upload JPEG, PNG or WebP images in Admin. Files are limited to 8 MiB and 20 million pixels,
decoded, re-encoded without metadata and stored using generated WebP filenames and responsive sizes.
Never serve `MEDIA_ROOT` with WhiteNoise in production. Separate media hosting remains a deployment
task. Replaced/deleted records retain their older files; no automatic destructive media cleanup exists.

## Production preparation

Production preparation is complete as code; no public service is deployed. Follow
[the deployment handoff](docs/deployment.md) for the tested container, proxy, persistence and remaining
hosting decisions. Production requires an HTTPS canonical origin and a separate HTTPS media hostname.

```bash
npm ci --ignore-scripts
npm run css:build
uv sync --locked --no-dev
uv run --locked --no-dev --env-file .env.production manage.py collectstatic --noinput
uv run --locked --no-dev --env-file .env.production manage.py check --deploy
```

Set `DJANGO_SETTINGS_MODULE=config.settings.production` in the private deployment environment.
Use `--settings=config.settings.production` if explicitly checking that module from a local environment.
Production database connections use `sslmode=verify-full`; configure the provider's CA certificate.
Production credentials must not have the local role's `CREATEDB` privilege.

HSTS is intentionally off until HTTPS is verified. `check --deploy` will warn until that decision
is completed. Proxy-header trust is opt-in and requires a trusted proxy that overwrites forwarding headers.
Admin login throttling, Gunicorn, dependency audits and a non-root image are implemented. Actual TLS,
hosted PostgreSQL/media, proxy trust, backup/restore, scheduling and public deployment review remain
required. HSTS checks and their intentional staged warnings are explained in the deployment guide.

For a local non-debug performance lab after building CSS and static files:

```bash
uv run --locked python scripts/build_static.py
uv run --locked --env-file .env gunicorn --env DJANGO_SETTINGS_MODULE=config.settings.review \
  --bind 127.0.0.1:8001 --config deploy/gunicorn.conf.py config.wsgi:application
```

The review settings serve validated generated media locally, with production-style asset headers.
They use HTTP cookies/local PostgreSQL and must stay on loopback. Never deploy that module publicly.
The normal development server remains at port 8000.

## Further documentation

- [Architecture and phase boundaries](docs/architecture.md)
- [Security controls and limitations](docs/security.md)
- [Design direction](docs/design-system.md)
- [Asset licenses](docs/asset-licenses.md)
- [Third-party notices](docs/third-party-notices.md)
- [Executed Phase 2 checks](docs/phase-2-validation.md)
- [Phase 3 browser QA and validation](docs/phase-3-validation.md)
- [Phase 4 catalog validation and browser QA](docs/phase-4-validation.md)
- [Phase 5 shopping validation and browser QA](docs/phase-5-validation.md)
- [Phase 6 audit results and acceptance limits](docs/phase-6-validation.md)
- [Merchandising refinement and executed checks](docs/merchandising-validation.md)
- [Production deployment handoff](docs/deployment.md)

Each development phase ends with checks and owner review. Commits and pushes are left for owner review.
