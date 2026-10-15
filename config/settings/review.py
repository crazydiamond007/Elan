"""Local performance lab only: non-debug, hashed static files, loopback HTTP/database.

This module is not a public deployment configuration. Serve only on 127.0.0.1.
"""

from config.env import required

from .base import *  # noqa: F403

SECRET_KEY = required("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
SITE_URL = "http://127.0.0.1:8001"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
LOCAL_REVIEW = True
DATABASES["default"]["OPTIONS"]["sslmode"] = "disable"  # noqa: F405
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
