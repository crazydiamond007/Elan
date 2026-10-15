# Architecture

Approved direction: a Django monolith with PostgreSQL, templates, progressive enhancement,
Tailwind's standalone CLI, English interface text and EUR pricing.

## Phase 2 implementation

`config` owns settings and URL composition. `accounts.User` extends Django's `AbstractUser`
without additional fields, established before the first migration. `core` owns the public shell,
demo disclosure, no-index policy and generic error responses. Django Admin handles authenticated
content management; only user/group management exists at this phase.

Views handle HTTP behavior. Environment parsing lives in `config/env.py`; it is strict and avoids
including configuration values in error messages. Settings use environment variables directly;
uv's `--env-file` loads local configuration without another dotenv dependency.

The private local database is `maison_elan`, owned by a dedicated non-superuser role. The local role
has `CREATEDB` solely for PostgreSQL tests. Production provisioning must remove that privilege.
The existing native PostgreSQL service was reused; no cluster configuration was changed.

## Application responsibilities

| Application | Intended phase | Responsibility |
| --- | --- | --- |
| `catalog` | 4, implemented | Models, images, publication rules, querysets and admin |
| `cart` | 5, implemented | Session-based quantities, stock validation and server-side totals |
| `checkout` | 5, implemented | Fictional details, final revalidation and session-bound demo confirmation |
| `marketing` | 5, implemented | Newsletter forms, local fictional persistence and abuse controls |

`core` also provides shared PostgreSQL abuse counters. No extra infrastructure or package was added.

## Phase 3 presentation

Shared Django template components supply navigation, footer, image markup, product-preview cards,
newsletter presentation and small SVG arrows. A native `details` navigation menu works without
JavaScript; an external script adds Escape dismissal, outside dismissal and focus handling.

`core/editorial.py` holds four immutable presentation fixtures with Decimal illustrative prices.
Read-only `/collection-preview/` routes provide meaningful destinations while the database catalog
is pending. These fixtures cannot be added to a cart or submitted to checkout. New arrivals and the
signature edit use the same card component. Best-seller placements are explicitly curated demo content.

The newsletter is a disabled fieldset outside a form, with a visible coming-soon notice. It does not
submit or persist input. Supporting story, care, sizing and demo pages keep footer links meaningful.
At the end of Phase 3, catalog management and customer submissions were still unimplemented.

Pillow became a runtime dependency in Phase 4 for managed uploads. Image masters and generated-image
prompts are versioned; all visitor assets are local. Temporary browser QA dependencies live under `/tmp`.

## Domain decisions

- Products hold descriptions, department, category membership and publication state.
- Collections provide campaign groupings; department and product category remain distinct.
- Variants hold unique SKUs, size, color, Decimal prices and inventory.
- Images have ordering and alt text, with optional color association.
- Database constraints defend nonnegative amounts/stock and variant uniqueness.
- Filtering must match size, color, price and availability on the same eligible variant.
- New arrivals derive from publication dates; sale derives from pricing.
- Featured and best-selling placements are curated demo merchandising, without fabricated sales claims.
- Cart sessions store identifiers and quantities, never authoritative client prices.
- Demo checkout does not take payment, create a genuine order, or decrement stock.
- Accounts and wishlists can refer to the custom user later; no customer authentication UI exists now.

Apply migrations for schema changes. Add indexes for observed access patterns, and use
`select_related`, `prefetch_related`, bounded search and pagination. Keep business services simple;
no API, generic repository layer, worker queue, Redis or microservices are currently required.

## Phase 4 catalog

`catalog.Product` belongs to one protected category and any number of collections. Women, men,
unisex and accessories are product departments; a unisex product appears in both women and men.
Sizes and colours are reusable managed records. `Variant` owns price, optional original price,
stock and unique SKU, with a unique product/colour/size combination. EUR is the single currency.
Money uses `DecimalField`; positive-price, valid-sale-price and nonnegative-stock constraints are
enforced by PostgreSQL. Published records require a date; future dates schedule visibility.

`ProductQuerySet.public()` centralizes publication, active-category and active-variant rules.
Sold-out variants remain visible with an explicit unavailable state. `for_display()` selects the
category and prefetches active variants/options and ordered images; presentation properties use
those prefetched lists. Listings paginate at twelve products and reject invalid/out-of-range pages.
New arrivals order by reached publication dates; sale uses an eligible variant's original price.
Collections and category URLs reject unpublished groupings rather than falling back to all products.

Phase 4 product detail selection used a read-only GET form. Colour and size must belong to the
same active variant; quantity is bounded and checked against positive stock. Selection can display
an unavailable size, but cannot submit a purchase. Price always comes from the selected database
variant. Gallery images optionally belong to colours; multiple uploaded images appear in their
managed order with native anchor navigation. Missing photography has an explicit placeholder.

Admin uses model permissions, searchable records, filters, product variant/image inlines and a
separate inventory list. There is no seeded administrator. `seed_catalog` creates only new products
from the original licensed capsule and does not reset existing merchandising or inventory.

`catalog/images.py` bounds, validates, decodes and strips metadata from staff uploads. Model saves
generate responsive WebP files; UUID paths discard untrusted filenames. File storage and database
transactions are not jointly atomic: an enclosing database rollback can leave unreferenced files.
Older files are retained on replacement/deletion. A reviewed maintenance policy and separate media
hosting belong to deployment preparation; there is no automatic file deletion service.

## Phase 5 shopping

`catalog/search.py` applies search/filter rules with correlated ORM queries. Category is a product
filter; size, colour and Decimal price bounds must match one active variant. Sale eligibility also
matches that variant. Display prefetches use the eligible set so card prices describe the selected
options. SKU searches consider eligible variants only. Sort choices are an explicit allowlist;
price ordering uses a correlated minimum eligible price and a stable primary-key tie-breaker.
Pagination retains active query parameters. Invalid input returns HTTP 400 with field feedback.

Product selection now uses a CSRF-protected native POST form. Its secondary submit button previews
options at the product URL; its main button submits to the cart. Existing GET selection links still
work. The submitted options resolve to one public, active database variant. There is no client price.

`cart/services.py` bounds and normalizes a JSON session dictionary of variant IDs and quantities
(twenty lines, ten units per variant). Public variant queries recheck publication/category state and
stock; one image prefetch avoids queries per cart line. Snapshots use Decimal totals. Missing or
unpublished lines show a generic unavailable label without leaking draft names. GET rendering does
not silently remove inventory conflicts: shoppers can reduce quantities or remove affected lines.

`checkout/services.py` records a review fingerprint of variant IDs, quantities and current prices.
Completion checks a session-held random token, locks eligible variant rows, revalidates the cart and
rejects price/quantity changes until reviewed again. `DemoReceipt` stores a fictional immutable
presentation snapshot, Decimal subtotal and an HMAC session association, with a unique submission
token. Duplicate submissions return the same receipt; historical replay does not clear a new bag.
Confirmation lookup checks the current session hash. No real order, stock decrement, customer form,
address, card or external payment request exists.

Django's database session backend is retained. At the Phase 5 boundary it allowed concurrent cart
overwrites; Phase 6 wraps established shopping-session mutations and middleware persistence in a
row lock. Session retention and secret rotation still affect confirmation accessibility.

Newsletter forms and model validation accept reserved example domains only. Signups are normalized,
unique, local and produce the same feedback for duplicate input. No email is sent. Staff model
permissions govern Admin access. Demo records stay until owner removal; no retention automation is
implied. `core/rate_limits.py` uses HMAC keys and PostgreSQL conditional updates for shared fixed-window
counters. Limits are 60 cart changes/minute, 10 checkout attempts/10 minutes and 5 newsletter
attempts/10 minutes per socket client address. A dedicated command prunes expired counters.

The header links to search and bag without loading a cart count on every page. Feedback is rendered
only on pages that need it, preserving database-free generic error rendering. Bag, checkout,
confirmation and newsletter responses are private/no-store. Forms and disclosures require no JS.

## Phase 6 preparation

`ShoppingSessionLockMiddleware` runs outside SessionMiddleware for cart/checkout POST paths only,
so existing-session reads and writes share one transaction/row lock. Public product presentation
establishes the session first. Ordinary GET/error paths do not acquire locks. Regression tests use
separate concurrent database connections; no generic custom session backend or infrastructure is added.

`TrustedClientAddressMiddleware` validates exact proxy peer networks and a single overwritten client
address. Shared counters now include admin login attempts after CSRF. New liveness/readiness views
expose only a generic state; the former is database-free. A sitemap uses configured canonical origins
and shared public querysets. Open Graph/WebSite/Product metadata preserves the fictional/no-index
boundary and omits commercial offers, private URLs and fabricated ratings.

Product image dimensions come from the versioned editorial manifest. Expanded WebP sizes and modest
compression reduce selection gaps. Django gzip, immutable asset headers and a non-debug local
Gunicorn review profile support measured lab audits. No shared full-page HTML cache is introduced.

Production artifacts use the locked uv/npm build, digest-pinned multi-stage images and a non-root
Gunicorn runtime. PostgreSQL and media/TLS hosting are external deployment choices. The example proxy
serves generated media from a distinct host. `docs/deployment.md` gives the concrete handoff; examples
are not installed services or an authorization to deploy. Operator infrastructure acceptance remains
necessary even after local checks pass.

## Review boundaries

Phase 3 defines the complete visual system and editorial homepage. Phase 4 supplies real catalog
queries and licensed product imagery. Phase 5 completes the shopping journey. Phase 6 measures
accessibility/performance and reviews production security, SEO and hosting.

Temporary merchandising in Phase 3 must be identified as such. Functional completion requires
working routes, validated forms and tests; visual placeholders do not imply complete features.
