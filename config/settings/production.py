"""Deployment scaffold; infrastructure and deployment require a separate review."""

import os
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from config.env import boolean, comma_list, https_origin, integer, proxy_networks, required

from .base import *  # noqa: F403

SECRET_KEY = required("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be a strong, deployment-specific secret.")

DEBUG = False
ALLOWED_HOSTS = comma_list("DJANGO_ALLOWED_HOSTS", mandatory=True)
if not ALLOWED_HOSTS or any(
    "*" in host or "/" in host or host.startswith(".") for host in ALLOWED_HOSTS
):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain explicit hostnames.")

SITE_URL = https_origin(required("DJANGO_SITE_URL"), name="DJANGO_SITE_URL")
MEDIA_ORIGIN = https_origin(required("DJANGO_MEDIA_ORIGIN"), name="DJANGO_MEDIA_ORIGIN")
if urlsplit(MEDIA_ORIGIN).hostname == urlsplit(SITE_URL).hostname:
    raise ImproperlyConfigured("DJANGO_MEDIA_ORIGIN must use a separate hostname.")
MEDIA_URL = MEDIA_ORIGIN + "/"
CONTENT_SECURITY_POLICY["DIRECTIVES"]["img-src"] = ["'self'", MEDIA_ORIGIN]  # noqa: F405
TRUSTED_PROXY_NETWORKS = proxy_networks("DJANGO_TRUSTED_PROXY_NETWORKS")
if urlsplit(SITE_URL).hostname not in ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_SITE_URL must use a hostname in DJANGO_ALLOWED_HOSTS.")
CSRF_TRUSTED_ORIGINS = [
    https_origin(origin, name="DJANGO_CSRF_TRUSTED_ORIGINS")
    for origin in comma_list("DJANGO_CSRF_TRUSTED_ORIGINS")
]

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^healthz/$"]
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None
# Opt in only when the trusted proxy overwrites incoming forwarding headers.
if boolean("DJANGO_TRUST_PROXY_HTTPS"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Enable gradually after HTTPS is verified. No implicit preload or subdomain commitment.
SECURE_HSTS_SECONDS = integer("DJANGO_HSTS_SECONDS", default=0, maximum=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

DATABASES["default"]["OPTIONS"]["sslmode"] = "verify-full"  # noqa: F405
if root_certificate := os.environ.get("POSTGRES_SSLROOTCERT"):
    DATABASES["default"]["OPTIONS"]["sslrootcert"] = root_certificate  # noqa: F405

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
