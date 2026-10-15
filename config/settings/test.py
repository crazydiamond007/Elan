"""Tests exercise PostgreSQL and CSRF under non-debug settings."""

from .base import *  # noqa: F403

SECRET_KEY = "test-only-key-not-for-deployment"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
SITE_URL = "http://testserver"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
STATIC_ROOT = None
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
DATABASES["default"]["OPTIONS"]["sslmode"] = "disable"  # noqa: F405
