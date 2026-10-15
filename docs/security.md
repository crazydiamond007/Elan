# Security controls and deployment boundaries

This document describes implemented foundation controls and remaining work. It is not a
security certification or a claim that the application is invulnerable.

## Implemented

- Django CSRF middleware is enabled; admin login/logout use protected forms.
- Listings accept GET/HEAD; shopping changes and newsletter persistence require CSRF-protected POST.
- Template autoescaping remains enabled. No rich HTML content or `safe` filter is introduced.
- PostgreSQL access uses Django/psycopg; provisioning uses parameterized queries and SQL identifiers.
- Database sessions use HttpOnly, SameSite=Lax session cookies.
- Admin requires active staff authentication and model permissions. Staff status alone does not
  grant user management permissions. Password validators are enabled.
- The local role has no superuser, role-administration or replication permission.
- Secrets are loaded from environment variables. The helper creates `.env` with mode `0600`
  and refuses to replace it. Secrets and runtime files are ignored by Git.
- CSP denies unspecified sources, objects and framing. Scripts/styles/fonts/images are self-hosted.
  Inline script attributes and eval are not enabled.
- A minimal Django admin change-list override supplies a nonce for Django's conditional inline
  style. Its test verifies the nonce matches the response policy. Recheck it on Django upgrades.
- `DENY` framing, `nosniff`, and a strict-origin-when-cross-origin referrer policy are configured.
- HTML, errors and application-served static files receive demo no-index headers. Pages also
  include robots metadata; `robots.txt` disallows crawling. This is not access control.
- Generic non-debug error responses do not expose exception details. Error pages omit canonicals.
- Request-body and in-memory upload thresholds and a twenty-file request limit are configured.
  Proxy upload limits remain necessary; these settings are not a total multipart body-size limit.
- The email backend is in-memory; the foundation cannot send external email.

## Phase 3 presentation controls

At the Phase 3 boundary, homepage/supporting previews were read-only GET/HEAD endpoints and
newsletter input was disabled. Product-preview prices were illustrative server-side Decimal values.
Phase 5 replaced that boundary with the protected shopping forms described below; payment/account
forms remain absent.

All fonts, scripts and images are local. No CSP relaxations, external trackers, eval, unsafe HTML
rendering, inline event handlers or animation libraries were introduced. Navigation JavaScript is an
external progressive enhancement over native `details` behavior. Browser QA found no unexpected
external asset requests or CSP/JavaScript errors across the tested home-page viewports.

The editorial image build helper operates on trusted versioned masters. Phase 4 added a separate
runtime validation path for staff uploads, described below.

## Phase 4 catalog controls

Phase 4 listings/details and selection forms were GET/HEAD only. ORM queries apply shared
publication rules, select only active variants and never trust a browser-supplied price. Invalid
selections return HTTP 400 with an accessible error summary; invalid pages/groupings return 404.
Sold-out sizes are clearly unavailable. The cart became functional in Phase 5. PostgreSQL constraints
defend variant uniqueness, positive prices, valid sale prices and nonnegative inventory.

Catalog administration requires active staff authentication and per-model permissions. Uploads have
no public endpoint. JPEG, PNG and WebP uploads are bounded at 8 MiB and twenty million pixels, require
at least 100 pixels per side, reject animation, verify structure and fully decode. Input filenames,
claimed MIME types and extensions do not authorize a file. Model saves independently repeat safe
processing so they cannot bypass it by omitting `full_clean()` for a newly assigned file.

Admin uses a bounded file form before Pillow verification, and rejected/truncated files produce form
errors before saving. Images are orientation-corrected, flattened, re-encoded into fresh WebP pixels
without EXIF/XMP/ICC metadata, and written as responsive derivatives under generated UUID names.
Original uploaded containers are not persisted or served. Required alt text is validated by forms.
Failed individual saves clean up their newly generated files. An outer transaction rollback can
still leave orphaned files because filesystem storage is not transactional. Old files are retained
on replacement/deletion; a safe cleanup/retention policy requires a later explicit review.

Local media is served through Django only in development. Sanitizing images does not establish a
complete upload security boundary: production needs a separate cookie-free media origin, suitable
content types/headers, proxy byte limits, storage permissions and reviewed CSP origin configuration.

## Phase 5 shopping controls

Search text, option values, Decimal prices and sort choices are validated server-side. Duplicate
filter parameters, non-finite prices, oversized text and reversed ranges are rejected. SQL remains
ORM-generated; templates escape all query and catalog content. Size, colour, price and sale criteria
match the same active variant. Catalog pagination stays bounded and maintains filters.

Cart sessions store identifiers/quantities only. Every change resolves an active, published variant
and checks stock, twenty-line capacity and ten-unit limits. Rendering and checkout re-read prices;
hidden/deleted items receive generic unavailable labels. Cart changes, selection previews, checkout
completion and newsletter submissions require CSRF. Mutating cart URLs reject GET/HEAD.

Checkout uses reviewed fingerprints, random tokens, variant row locks and a unique receipt token.
It rechecks availability/prices, requests a new review when amounts change, and returns the same
receipt for duplicate submissions. Tests cover concurrent duplicate submission. Confirmation URLs
also require the matching HMAC session association; knowing the UUID alone does not grant access.
No browser-supplied totals, personal checkout data or payment details are persisted. Completion does
not change inventory. Bag/checkout/confirmation/newsletter responses use private, no-store headers.

Newsletter input is restricted to reserved addresses, normalized and unique. Repeated valid input
gets the same feedback. No email integration is configured. Demo signup and receipt records remain
locally until the owner removes them; no automated retention guarantee is made.

POST abuse limits use shared PostgreSQL counters with atomic conditional increments; concurrency is
tested. Keys are HMAC hashes of endpoint scope, socket client address and time window, with no raw
IP stored in the table. Limits: cart 60/minute, checkout 10/10 minutes, newsletter 5/10 minutes.
429 responses include Retry-After. Forwarded IP headers are ignored; production must establish
trusted proxy client-address handling and schedule `prune_rate_limits`. Fixed windows can allow
bursts at boundaries and do not stop distributed abuse. Infrastructure protection remains necessary.

At the Phase 5 boundary, independent session writes could overwrite concurrent cart edits and admin
login protection was pending. Phase 6 closes those application gaps as described below. No public
deployment is approved.

## Phase 6 review and hardening

Shopping POSTs with an established session hold a PostgreSQL session-row lock around both session
loading and middleware persistence. Product pages create that shopping session before submission.
Parallel additions and duplicate checkout are tested with real concurrent database connections.
State-changing requests without an existing cookie cannot rely on merging independent sessions.

Administration login POSTs now have a shared limit of ten attempts per ten minutes, checked after
CSRF. Passwords/entered credentials are never included in throttle responses. Trusted client-address
handling accepts one X-Real-IP only from configured socket peer CIDRs; forwarding lists, invalid
addresses and untrusted peers cannot supply an identity. Catch-all networks are rejected in production.
This is a small application control, not complete protection from distributed credential attacks.

Production requires a distinct HTTPS media hostname and adds only that origin to image CSP. Cookies
stay host-only. CSP retains self/nonces, denies arbitrary inline handlers and eval, and nonce-encodes
the escaped JSON-LD data block. JSON metadata uses Django's serializer to escape HTML breakouts.
There are no Product offers/ratings for fictional goods. Private/error pages omit canonicals and
social metadata; sitemap data excludes private, draft, future and inactive content.

HTML responses are private/no-cache to prevent shared reuse of per-response nonces and CSRF tokens.
Personalized responses additionally remain no-store. Django's gzip adds randomized padding rather
than naive dynamic compression; hashed static files and generated immutable media use long cache
lifetimes. The local review settings emulate asset policies on loopback, without deployed TLS.

Rendered Admin review found label/target issues and fixed them with named variant/date controls,
native collection/date widgets, visible breadcrumb underlines and larger filter targets. Its isolated
axe audit supplies the response nonce to the audit tool's own CSS probes; application policy is not
relaxed. Login/edit/upload/logout and storefront journeys passed without application CSP errors.

Gunicorn 26.2.0 is the production WSGI server. The container runs UID 10001 with a read-only root,
restricted volume/tmp writes, dropped capabilities, no privilege escalation and digest-pinned build
images. Locked requirements and npm dependencies were audited with no known vulnerabilities reported
at the recorded check time. OS/native-library auditing is a separate release responsibility.
The clean image was smoke-tested without external networking or host mounts, using dummy settings.

Production HTTPS/database/media connectivity, scheduler/retention/backup policies and image lifecycle
have not been deployed or verified. HSTS remains deferred until real HTTPS is established; staged
checks intentionally leave broad-subdomain/preload warnings. See `deployment.md` and Phase 6 validation.

## Local development

Development uses `DEBUG=True`, explicit loopback hosts, HTTP cookies and loopback PostgreSQL
without TLS. Bind the development server to `127.0.0.1`. Do not expose development settings publicly.
Django's debug 404/500 pages may display diagnostics; django-csp also exempts debug 404/500 responses.

The WSL administrative database account can provision the project, but the application uses its
dedicated role. Local tests use `config.settings.test`, non-debug rendering and a disposable
PostgreSQL test database. They do not exercise real TLS infrastructure.

## Production scaffold

- `DEBUG=False`, deployment-specific strong secret, explicit hostnames and HTTPS site URL.
- Secure session/CSRF cookies and HTTPS redirects are enabled.
- Database TLS uses `verify-full`, including hostname and certificate verification.
- WhiteNoise serves hashed, gzip-compressed static assets after `collectstatic`.
- Proxy HTTPS-header trust is disabled by default. Enable only after verifying that a trusted
  proxy strips/overwrites client forwarding headers.
- HSTS defaults to zero until HTTPS is established. Enable gradually; subdomains/preload are
  deliberately not implicit. Django's deployment check warns about this initial state.
- The no-index policy remains active on the deployed demo.

There is no production web server, hosted database, public domain, media service or deployment yet.
Local file media storage is a placeholder; WhiteNoise must not serve user uploads in production.

## Required in later phases

- Catalog deployment: separate media serving, byte limits at the proxy and a reviewed orphan-file
  retention/cleanup policy. Bulk ORM writes and direct storage manipulation must never handle uploads.
- Shopping deployment: verify serialized session behavior, lifecycle and real hosted cookie/TLS behavior.
- Abuse controls: verify trusted peer addresses, schedule counter pruning and establish infrastructure
  controls before public exposure. Application admin login throttling is implemented.
- Newsletter deployment: maintain reserved-address policy and define any future retention automation;
  collecting real addresses would require explicit scope approval.
- Deployment: least-privilege database credentials, HTTPS/proxy/HSTS verification, refreshed audits,
  backup/restore review, redacted logging, safe 500 responses and `manage.py check --deploy`.
- Browser review: Chrome/Firefox and rendered Admin checks are complete for the recorded scenarios.
  Physical screen-reader and Safari/iOS review remain acceptance checks; HTTP tests and automated
  scans do not establish full accessibility conformance.

The Tailwind audit originally identified the braces stack-exhaustion advisory in a watcher
dependency. Matching Tailwind 4.3.0 packages permit the fixed watcher 2.6.0. The final lockfile
passed npm's audit when generated; new advisories can appear and updates require review.

References: [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/),
[Django security guidance](https://docs.djangoproject.com/en/5.2/topics/security/),
[django-csp configuration](https://django-csp.readthedocs.io/en/latest/configuration.html).
