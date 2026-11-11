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

## Single-service hosted deployment

The Compose arrangement above assumes two origins and a shared media volume. A single-service
host - one container, one domain, one attached volume - cannot provide that, so two settings
make the difference explicit rather than leaving it implied.

`DJANGO_SERVE_MEDIA=true` drops the separate media origin. `MEDIA_URL` becomes `/media/`, the
image policy stays at `'self'`, and `config/urls.py` adds one route that matches only generated
product WebP names. Nothing else under `MEDIA_ROOT` is reachable, no user-supplied filename ever
appears in a URL, and the view is confined to `MEDIA_ROOT/products` and to safe methods. A
separate origin is still preferable where the host can provide one, because it keeps uploaded
bytes off the application origin entirely; this is the documented trade for hosts that cannot.

`POSTGRES_SSLMODE` selects server verification. `verify-full` stays the default. `verify-ca`
proves the chain but skips the hostname check, for providers whose certificate names do not cover
the hostname you connect to; it requires `POSTGRES_SSLROOTCERT`. `require` encrypts without
authenticating the server at all and is defensible only when the database is reachable solely over
the provider's private network. `prefer`, `allow` and `disable` are refused, so no configuration
can silently produce an unencrypted connection.

Media must still outlive a redeploy. Attach a persistent volume at `MEDIA_ROOT` (`/app/media`), or
set the `MEDIA_BUCKET_*` variables to keep generated media in any S3-compatible bucket instead.
Without one of the two, a restart serves a catalog whose images have been discarded.

### Railway

`railway.json` pins the build and deploy settings: the repository `Dockerfile`, `/healthz/` as the
health check, and a bounded restart policy. It cannot express variables or volumes, so those are
set on the service itself.

Create the project, add a PostgreSQL database to it, and attach a volume to the application
service mounted at `/app/media`. Generated product derivatives live there, and a container
filesystem is replaced on every redeploy, so without the volume the catalog returns with its
images missing. A service with a volume cannot run replicas, and redeploying it involves brief
downtime even with a health check configured.

Set these variables on the application service. `${{Postgres.*}}` resolves against the database
service and assumes it is named `Postgres`; `${{RAILWAY_PUBLIC_DOMAIN}}` resolves to the generated
domain:

```
PORT=8000
WEB_CONCURRENCY=2
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<generate a unique value; never commit it>
DJANGO_ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}},healthcheck.railway.app
DJANGO_SITE_URL=https://${{RAILWAY_PUBLIC_DOMAIN}}
DJANGO_CSRF_TRUSTED_ORIGINS=https://${{RAILWAY_PUBLIC_DOMAIN}}
DJANGO_TRUST_PROXY_HTTPS=true
DJANGO_SERVE_MEDIA=true
DJANGO_HSTS_SECONDS=0
POSTGRES_HOST=${{Postgres.RAILWAY_PRIVATE_DOMAIN}}
POSTGRES_PORT=5432
POSTGRES_DB=${{Postgres.PGDATABASE}}
POSTGRES_USER=${{Postgres.PGUSER}}
POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
POSTGRES_SSLMODE=require
DJANGO_BOOTSTRAP_ON_START=true
DJANGO_SUPERUSER_USERNAME=<your administrator name>
DJANGO_SUPERUSER_PASSWORD=<a password that passes Django's validators>
DJANGO_SUPERUSER_EMAIL=<optional>
```

Generate the secret with `python -c 'import secrets; print(secrets.token_urlsafe(64))'`.

Three of these fail in distinctive ways. `PORT` matches the port the image binds; Railway health
checks the port it is told about, so a mismatch leaves the deployment permanently unhealthy rather
than reporting a useful error. `DJANGO_TRUST_PROXY_HTTPS` is required because TLS terminates at
the platform; without it every request redirects to itself. `DJANGO_ALLOWED_HOSTS` must contain
`healthcheck.railway.app` as well as the public domain, because health checks arrive with that
Host header and production settings answer an unlisted host with 400.

Railway's PostgreSQL template issues a self-signed certificate whose subject alternative name
covers only `localhost`, so `verify-full` and `verify-ca` both fail against it without rebuilding
the template's certificate. The service therefore reaches the database over the project's private
network with `POSTGRES_SSLMODE=require`, using the database's `RAILWAY_PRIVATE_DOMAIN` rather than
its public TCP proxy. Pointing the application at a provider that publishes a conventional chain
instead allows the default to stand.

### Bootstrapping on start

The policy above keeps migrations manual, because a reviewed deployment should apply them
deliberately and against a known backup. A platform that offers no separate migration step cannot
honour that, so `DJANGO_BOOTSTRAP_ON_START=true` opts a deployment into running
`manage.py bootstrap_deployment` from `deploy/entrypoint.sh` before Gunicorn starts. Unset, the
entrypoint does nothing and the Compose deployment behaves exactly as documented above.

The command applies migrations, seeds the demonstration catalog and creates an administrator. It
runs on every container start, so every stage is idempotent: migrations are no-ops once applied,
and the three seed commands skip records that already exist. A failure stops the container rather
than letting it serve a half-configured application.

This runs at container start rather than through a platform pre-deploy hook on purpose. Seeding
writes generated media to `MEDIA_ROOT`, and only the real container start is guaranteed to have
the persistent volume attached; a pre-deploy hook could seed into the image layer instead, leaving
catalog rows that point at files the running container cannot see.

The administrator comes from `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD` and the
optional `DJANGO_SUPERUSER_EMAIL`. The password passes Django's validators, so a weak one fails the
deployment instead of creating an account that cannot be defended. An existing account is never
modified: a password changed through the admin survives the next restart, and the variable is a
starting point rather than a standing instruction to overwrite.

To run any of these manually instead, use `railway ssh --`, which executes inside the container.
`railway run` executes locally with the service's variables and cannot resolve the private
database hostname.

Check `/healthz/` first: it touches no database and is exempt from the HTTPS redirect, so it
isolates "the platform reached the application" from "the application reached PostgreSQL". Then
check `/readyz/`, which runs a trivial query and returns a generic 503 when the database is
unreachable. Then load a catalog page to confirm media URLs resolve.

`DJANGO_TRUSTED_PROXY_NETWORKS` stays empty until the platform's proxy peer address is known.
Until it is set, rate limits key on that proxy address rather than the visitor's, which makes them
global rather than per-client.
