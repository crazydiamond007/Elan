#!/bin/sh
# Container entrypoint. Bootstrapping runs here rather than in a platform pre-deploy hook because
# seeding writes generated media to MEDIA_ROOT, and only the real container start is guaranteed to
# have the persistent volume mounted. A pre-deploy hook could seed into the image layer instead,
# leaving catalog rows that point at files the running container cannot see.
set -eu

if [ "${DJANGO_BOOTSTRAP_ON_START:-}" = "true" ]; then
  echo "Bootstrapping deployment"
  uv run --no-sync --no-dev python manage.py bootstrap_deployment
fi

exec "$@"
