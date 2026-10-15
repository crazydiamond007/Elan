# Production handoff

Phase 6 prepares deployment artifacts; it does not activate a public site. The repository contains
a pinned multi-stage Docker image, a restricted Compose web service, Gunicorn configuration and an
Nginx example. A host/provider, application domain, separate media hostname, database and real TLS
certificates must be selected and reviewed before deployment. Native WSL development remains unchanged.

## Runtime and build

Python 3.13.14, uv 0.11.28 and Node 24.18.0 base images are pinned by digest. The frontend stage
runs locked npm installation and Tailwind compilation. The Python stage uses `uv sync --locked --no-dev`.
Node, npm, project secrets, local media, Git history, development tools and QA profiles are excluded
from the runtime. Python package metadata retains dependency licenses; see third-party notices.

`scripts/build_static.py` generates a process-only random key and deliberately unusable build-time
database/origin values to run `collectstatic` without database access or real secrets. Those values
are not runtime configuration. Hashed/gzip static files are built into the image. Runtime UID/GID
is 10001, the filesystem is read-only except a media volume and `/tmp`, Linux capabilities are
dropped and privilege escalation is disabled. Gunicorn uses two sync workers, bounded recycling and
timeouts, with no management socket. Its logs omit query strings, bodies and cookies.

Prepare a private `.env.production` from `.env.example`, change its settings module to production
and replace placeholders. It must contain a distinct strong secret, explicit application hosts,
HTTPS canonical origin, HTTPS media origin with a different hostname, PostgreSQL credentials and
provider CA configuration. Media origin is required; production never serves uploads through Django
or WhiteNoise. Cookies stay host-only. Preserve the no-index policy for this demonstration.

`compose.production.yaml` binds the web service to host loopback, uses a persistent named media
volume and probes `/healthz/`. It intentionally does not provision a public proxy or database.
The entry command forces production settings even if a mistaken environment-file value says
development. Native production commands also need the explicit production settings module.

After a deployment target and credentials are approved, the intended commands are:

```bash
docker compose -f compose.production.yaml build
docker compose -f compose.production.yaml run --rm web uv run --no-sync --no-dev \
  python manage.py check --deploy --settings=config.settings.production
docker compose -f compose.production.yaml run --rm web uv run --no-sync --no-dev \
  python manage.py migrate --settings=config.settings.production
docker compose -f compose.production.yaml run --rm web uv run --no-sync --no-dev \
  python manage.py seed_catalog --extended --settings=config.settings.production
docker compose -f compose.production.yaml run --rm web uv run --no-sync --no-dev \
  python manage.py createsuperuser --settings=config.settings.production
docker compose -f compose.production.yaml up -d web
```

These are handoff instructions, not authorization to execute a deployment. No migrations or seeds
run automatically at container startup. Review migrations and take the appropriate backup first.
Use a dedicated production role without the local test role's CREATEDB privilege. Initial migration
privileges and routine runtime privileges should be reviewed separately. PostgreSQL TLS uses
`verify-full`; ensure the CA file is mounted read-only at its configured path inside the container.
The Compose example does not mount a provider certificate until its location is known.

## Proxy and media

`deploy/nginx.example.conf` is an HTTP-context example, not an installed service. Replace sample
domains, certificate locations and media-root paths. The media server needs a read-only mount of
the Compose media volume at `/srv/maison-media`; grant its worker read access to generated files.
The application retains write access through its volume. Nginx permits only generated WebP paths,
serves correct MIME/nosniff/no-index headers, disables listings and uses immutable cache headers.
There is no PHP/script handler, authentication cookie domain or uploaded-original serving.

The application proxy overwrites Host, X-Forwarded-Proto and X-Real-IP and clears X-Forwarded-For.
Backend ports remain private. Set `DJANGO_TRUST_PROXY_HTTPS=true` only for that verified proxy path.
Set `DJANGO_TRUSTED_PROXY_NETWORKS` to exact peer CIDRs, and any Gunicorn forwarding allowlist to
explicit peers. Container networking can make the socket peer a bridge gateway rather than
127.0.0.1; verify it on the chosen host before configuring trust. Unlisted peers and malformed or
multiple client addresses cannot override socket identity. Never use a catch-all network or `*`.

Django compresses dynamic HTML with randomized padding; WhiteNoise compresses static assets. Do not
introduce shared HTML caching: pages contain CSRF tokens and CSP nonces, and personalized responses
are private/no-store. The example logs method, path, status and duration only. Review infrastructure
logging separately before adding telemetry or third-party error reporting.

## HTTPS and deployment checks

Development/review servers use loopback HTTP. No certificate or hosted HTTPS has been established.
Production settings enforce secure cookies, redirects and database certificate verification. The
database-free liveness endpoint is exempt from redirects for internal probes; it exposes only an
`ok` state. `/readyz/` checks PostgreSQL and returns a generic 503 on failure without diagnostics.

HSTS starts at zero: Django reports W004 until HTTPS has been verified. An explicit initial value
such as 300 is supported; checks then report W005/W021 because includeSubDomains and preload stay
off. These are deliberate boundaries, not silenced checks. Do not enable broad/preload commitments
without verifying every affected domain. Increase duration only after real TLS/redirect review.

Before public activation, verify certificate renewal, proxy/header trust, host rejection, actual
Secure/HttpOnly/SameSite cookies, CSRF, media content types/CSP, and persistence across worker/service
restarts. The Docker smoke used dummy credentials and an HTTPS forwarding header in an isolated
network; it does not prove internet TLS or database connectivity. Nginx was parse-checked with QA
self-signed certificates only. Run package and container/base-library audits again near launch.

## Operations and remaining review

Schedule the commands below through the selected host's scheduler; neither is automatically installed:

```bash
uv run --locked --no-dev --env-file .env.production python manage.py clearsessions --settings=config.settings.production
uv run --locked --no-dev --env-file .env.production python manage.py prune_rate_limits --settings=config.settings.production
```

Rate limits are shared PostgreSQL fixed windows: cart 60/minute, checkout/admin login 10/10 minutes
and newsletter 5/10 minutes per verified client address. They do not replace infrastructure limits
or protection from distributed attacks. Use strong unique administrator passwords; decide whether
network restrictions or additional authentication are required for the selected public host.

Shopping changes for an established session serialize the session read/write and receipt creation.
Product pages establish that session before form submission. Test parallel tabs on the actual host;
clients submitting without a session cookie cannot expect cross-request cart merging. Sessions must
use the database backend unless equivalent concurrency behavior is explicitly reviewed.

Demo receipts and reserved-address signups have no automatic deletion policy. File replacement and
outer transaction rollbacks can retain unreferenced media. There is no destructive cleanup command.
Define retention, backup/restore and an orphan-file review policy before hosting; backup/restore has
not been exercised against a hosted provider. Restore databases and media together when necessary.
Image upload request sizes must also be bounded at the chosen edge: the example caps a multipart
request at 16 MiB, while application validation limits each image to 8 MiB/twenty million pixels.

Chrome/Firefox browser checks and automated audits are recorded in Phase 6 validation. Physical
screen-reader testing, Safari/iOS and real hosting measurements remain acceptance checks before
public activation; automated results are not accessibility certification or a security guarantee.
