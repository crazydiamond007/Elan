"""Local HTTP development only. Never deploy these settings publicly."""

from config.env import required

from .base import *  # noqa: F403

SECRET_KEY = required("DJANGO_SECRET_KEY")
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
SITE_URL = "http://127.0.0.1:8000"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
DATABASES["default"]["OPTIONS"]["sslmode"] = "disable"  # noqa: F405
