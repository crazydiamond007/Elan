#!/bin/sh
# Container entrypoint.
#
# Bootstrapping runs here rather than in a platform pre-deploy hook because seeding writes
# generated media to MEDIA_ROOT, and only the real container start is guaranteed to have the
# persistent volume mounted. A pre-deploy hook could seed into the image layer instead, leaving
# catalog rows that point at files the running container cannot see.
#
# A platform attaches that volume owned by root, which replaces the ownership the image set at
# build time, so the unprivileged runtime user cannot write to it. The entrypoint therefore starts
# as root only long enough to correct ownership, then drops to the runtime user for every command
# it runs. The application itself never executes as root.
set -eu

MEDIA_DIR=/app/media
APP_HOME=/home/maison
APP_UID=10001
APP_GID=10001
DROP_PRIVILEGES=""

if [ "$(id -u)" = "0" ]; then
  mkdir -p "$MEDIA_DIR" "$APP_HOME"
  chown -R "$APP_UID:$APP_GID" "$MEDIA_DIR"
  chown "$APP_UID:$APP_GID" "$APP_HOME"
  # setpriv changes the user but not the environment, and libpq reads TLS material from $HOME.
  # Left pointing at root's directory, a TLS connection fails on an unreadable certificate path.
  export HOME="$APP_HOME"
  DROP_PRIVILEGES="setpriv --reuid=$APP_UID --regid=$APP_GID --clear-groups"
fi

if [ "${DJANGO_BOOTSTRAP_ON_START:-}" = "true" ]; then
  echo "Bootstrapping deployment"
  # Unquoted on purpose: empty when already unprivileged, a command prefix when not.
  # shellcheck disable=SC2086
  $DROP_PRIVILEGES uv run --no-sync --no-dev python manage.py bootstrap_deployment
fi

# shellcheck disable=SC2086
exec $DROP_PRIVILEGES "$@"
