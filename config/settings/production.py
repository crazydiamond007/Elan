"""Deployment scaffold; infrastructure and deployment require a separate review."""

import os
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from config.env import boolean, comma_list, https_origin, integer, proxy_networks, required

from .base import *  # noqa: F403

SECRET_KEY = required("DJANGO_SECRET_KEY")
# Name the failing property. The value must never be echoed, but its length and variety are not
# themselves secret, and without them a rejected key is indistinguishable from a missing one.
if SECRET_KEY.startswith("django-insecure-"):
    _weakness = "it is the development placeholder Django generates"
elif len(SECRET_KEY) < 50:
    _weakness = f"it is {len(SECRET_KEY)} characters and at least 50 are required"
elif len(set(SECRET_KEY)) < 5:
    _weakness = f"it uses only {len(set(SECRET_KEY))} distinct characters"
else:
    _weakness = ""
if _weakness:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be a strong, deployment-specific secret: "
        f"{_weakness}. Generate one with: "
        "python -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )

DEBUG = False
ALLOWED_HOSTS = comma_list("DJANGO_ALLOWED_HOSTS", mandatory=True)
if not ALLOWED_HOSTS or any(
    "*" in host or "/" in host or host.startswith(".") for host in ALLOWED_HOSTS
):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must contain explicit hostnames.")

SITE_URL = https_origin(required("DJANGO_SITE_URL"), name="DJANGO_SITE_URL")
# A separate media origin remains the preferred arrangement: it keeps uploaded bytes off the
# application origin entirely. A single-service host gives one domain and one attached volume and
# cannot provide a second origin, so DJANGO_SERVE_MEDIA opts into serving generated media from
# this origin instead. config/urls.py then exposes one route that matches only generated product
# WebP paths, and the image pipeline is the only writer of those names.
SERVE_MEDIA = boolean("DJANGO_SERVE_MEDIA")
if SERVE_MEDIA:
    MEDIA_ORIGIN = None
    MEDIA_URL = "/media/"
    # img-src stays at 'self', which already covers same-origin media.
else:
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

# Full verification stays the default and the expectation. Some managed providers issue the
# database a self-signed certificate whose SAN does not cover the hostname you connect to, which
# verify-full correctly rejects; `verify-ca` still proves the chain but skips the hostname check.
# `require` encrypts without authenticating the server, so it is only defensible when the database
# is reachable solely over the provider's private network and never from the internet. Modes that
# would allow an unencrypted connection are refused outright.
POSTGRES_SSLMODES = ("verify-full", "verify-ca", "require")
DATABASE_SSLMODE = os.environ.get("POSTGRES_SSLMODE", "verify-full").strip() or "verify-full"
if DATABASE_SSLMODE not in POSTGRES_SSLMODES:
    raise ImproperlyConfigured(
        "POSTGRES_SSLMODE must be one of: " + ", ".join(POSTGRES_SSLMODES) + "."
    )
DATABASES["default"]["OPTIONS"]["sslmode"] = DATABASE_SSLMODE  # noqa: F405
if root_certificate := os.environ.get("POSTGRES_SSLROOTCERT"):
    DATABASES["default"]["OPTIONS"]["sslrootcert"] = root_certificate  # noqa: F405
elif DATABASE_SSLMODE == "verify-ca":
    raise ImproperlyConfigured("POSTGRES_SSLMODE=verify-ca requires POSTGRES_SSLROOTCERT.")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Object storage for uploads, as an alternative to a persistent volume. A container filesystem
# does not survive a redeploy, so a host without attached storage keeps generated media in an
# S3-compatible bucket instead of MEDIA_ROOT, read publicly through MEDIA_ORIGIN. Unset, media
# stays on MEDIA_ROOT, which expects either a mounted volume or DJANGO_SERVE_MEDIA.
if not SERVE_MEDIA and (media_bucket := os.environ.get("MEDIA_BUCKET_NAME", "").strip()):
    media_endpoint = https_origin(required("MEDIA_BUCKET_ENDPOINT"), name="MEDIA_BUCKET_ENDPOINT")
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": media_bucket,
            "endpoint_url": media_endpoint,
            "access_key": required("MEDIA_BUCKET_ACCESS_KEY_ID"),
            "secret_key": required("MEDIA_BUCKET_SECRET_ACCESS_KEY"),
            # Public reads come from MEDIA_ORIGIN, so URLs are unsigned and never expire.
            "custom_domain": urlsplit(MEDIA_ORIGIN).netloc,
            "querystring_auth": False,
            "url_protocol": "https:",
            # R2 has no ACLs; object visibility is a bucket-level setting.
            "default_acl": None,
            "region_name": os.environ.get("MEDIA_BUCKET_REGION", "auto"),
            "signature_version": "s3v4",
            "file_overwrite": False,
        },
    }
