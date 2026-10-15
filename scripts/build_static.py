"""Compile static assets in an isolated image build without application secrets or SQL.

These process-only values authorize no real server/database. Never use them at runtime.
"""

import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.update(
    DJANGO_SETTINGS_MODULE="config.settings.production",
    DJANGO_SECRET_KEY=secrets.token_urlsafe(64),
    DJANGO_ALLOWED_HOSTS="static-build.invalid",
    DJANGO_SITE_URL="https://static-build.invalid",
    DJANGO_MEDIA_ORIGIN="https://media-build.invalid",
    DJANGO_CSRF_TRUSTED_ORIGINS="",
    DJANGO_TRUSTED_PROXY_NETWORKS="",
    DJANGO_TRUST_PROXY_HTTPS="false",
    DJANGO_HSTS_SECONDS="0",
    POSTGRES_DB="unused_static_build",
    POSTGRES_USER="unused_static_build",
    POSTGRES_PASSWORD="unused_static_build",
    POSTGRES_HOST="127.0.0.1",
)

from django.core.management import execute_from_command_line  # noqa: E402

execute_from_command_line(["manage.py", "collectstatic", "--noinput"])
