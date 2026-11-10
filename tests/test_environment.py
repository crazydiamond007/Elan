import os
import subprocess
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured

from config import env


def test_required_environment_values_are_not_silently_defaulted(monkeypatch):
    monkeypatch.delenv("EXAMPLE_SETTING", raising=False)
    with pytest.raises(ImproperlyConfigured, match="EXAMPLE_SETTING"):
        env.required("EXAMPLE_SETTING")


@pytest.mark.parametrize("value", ["true", "YES", "1", "on"])
def test_boolean_accepts_explicit_true_values(monkeypatch, value):
    monkeypatch.setenv("EXAMPLE_SETTING", value)
    assert env.boolean("EXAMPLE_SETTING") is True


def test_invalid_boolean_does_not_expose_its_value(monkeypatch):
    monkeypatch.setenv("EXAMPLE_SETTING", "private-diagnostic-marker")
    with pytest.raises(ImproperlyConfigured) as error:
        env.boolean("EXAMPLE_SETTING")
    assert "private-diagnostic-marker" not in str(error.value)


@pytest.mark.parametrize("value", ["not-a-number", "-1", "65536"])
def test_invalid_or_out_of_range_port_is_rejected(monkeypatch, value):
    monkeypatch.setenv("EXAMPLE_SETTING", value)
    with pytest.raises(ImproperlyConfigured):
        env.integer("EXAMPLE_SETTING", default=5432, minimum=1, maximum=65535)


@pytest.mark.parametrize(
    "origin",
    [
        "http://demo.example.com",
        "https://*.example.com",
        "https://user:password@example.com",
        "https://example.com/path",
        "https://example.com?query=1",
        "https://example.com#fragment",
        "https://example.com:invalid",
    ],
)
def test_production_origins_reject_unsafe_values(origin):
    with pytest.raises(ImproperlyConfigured):
        env.https_origin(origin, name="EXAMPLE_SETTING")


def production_settings(extra_environment=None, removed=()):
    environment = os.environ.copy()
    # Public test fixtures, unrelated to the local database credentials.
    environment.update(
        DJANGO_SECRET_KEY="production-settings-test-" + "0123456789abcdef" * 4,
        DJANGO_ALLOWED_HOSTS="demo.example.com",
        DJANGO_SITE_URL="https://demo.example.com",
        DJANGO_MEDIA_ORIGIN="https://media.example.net",
        DJANGO_TRUSTED_PROXY_NETWORKS="",
        DJANGO_CSRF_TRUSTED_ORIGINS="https://demo.example.com",
        DJANGO_TRUST_PROXY_HTTPS="false",
        DJANGO_HSTS_SECONDS="0",
    )
    environment.update(extra_environment or {})
    for name in removed:
        environment.pop(name, None)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import config.settings.production as s; "
            "assert not s.DEBUG; "
            "assert s.SESSION_COOKIE_SECURE and s.CSRF_COOKIE_SECURE; "
            "assert s.SECURE_SSL_REDIRECT; "
            "assert s.DATABASES['default']['OPTIONS']['sslmode'] == 'verify-full'; "
            "assert not hasattr(s, 'SECURE_PROXY_SSL_HEADER'); "
            "assert not s.SECURE_HSTS_INCLUDE_SUBDOMAINS; "
            "assert not s.SECURE_HSTS_PRELOAD; "
            "print('Production configuration validated')",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_production_settings_require_https_and_secure_cookies():
    result = production_settings()
    assert result.returncode == 0, result.stderr
    assert "Production configuration validated" in result.stdout


@pytest.mark.parametrize(
    "name",
    [
        "DJANGO_SECRET_KEY",
        "DJANGO_ALLOWED_HOSTS",
        "DJANGO_SITE_URL",
        "DJANGO_MEDIA_ORIGIN",
        "POSTGRES_PASSWORD",
    ],
)
def test_production_fails_on_missing_required_configuration(name):
    result = production_settings(removed=(name,))
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
    assert name in result.stderr


@pytest.mark.parametrize(
    "extra_environment",
    [
        {"DJANGO_ALLOWED_HOSTS": "*"},
        {"DJANGO_SECRET_KEY": "short"},
        {"DJANGO_SITE_URL": "http://demo.example.com"},
        {"DJANGO_SITE_URL": "https://different.example.com"},
        {"DJANGO_CSRF_TRUSTED_ORIGINS": "http://demo.example.com"},
        {"DJANGO_HSTS_SECONDS": "-1"},
        {"DJANGO_MEDIA_ORIGIN": "https://demo.example.com"},
        {"DJANGO_MEDIA_ORIGIN": "http://media.example.net"},
        {"DJANGO_TRUSTED_PROXY_NETWORKS": "0.0.0.0/0"},
        {"DJANGO_TRUSTED_PROXY_NETWORKS": "::/0"},
        {"DJANGO_TRUSTED_PROXY_NETWORKS": "invalid"},
    ],
)
def test_production_rejects_unsafe_configuration(extra_environment):
    result = production_settings(extra_environment)
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr


def database_sslmode(extra_environment):
    """Load production settings and report the resolved libpq TLS options."""
    environment = os.environ.copy()
    environment.update(
        DJANGO_SECRET_KEY="production-settings-test-" + "0123456789abcdef" * 4,
        DJANGO_ALLOWED_HOSTS="demo.example.com",
        DJANGO_SITE_URL="https://demo.example.com",
        DJANGO_MEDIA_ORIGIN="https://media.example.net",
        DJANGO_TRUSTED_PROXY_NETWORKS="",
        DJANGO_CSRF_TRUSTED_ORIGINS="https://demo.example.com",
        DJANGO_TRUST_PROXY_HTTPS="false",
        DJANGO_HSTS_SECONDS="0",
    )
    environment.pop("POSTGRES_SSLMODE", None)
    environment.pop("POSTGRES_SSLROOTCERT", None)
    environment.update(extra_environment)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import config.settings.production as s; "
            "o = s.DATABASES['default']['OPTIONS']; "
            "print(o['sslmode'], o.get('sslrootcert', '<unset>'))",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_database_tls_verifies_the_server_by_default():
    result = database_sslmode({})
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["verify-full", "<unset>"]


def test_verify_ca_is_available_for_providers_with_mismatched_certificate_names():
    result = database_sslmode(
        {"POSTGRES_SSLMODE": "verify-ca", "POSTGRES_SSLROOTCERT": "/etc/ssl/certs/ca.pem"}
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["verify-ca", "/etc/ssl/certs/ca.pem"]


def test_verify_ca_without_a_certificate_authority_is_refused():
    result = database_sslmode({"POSTGRES_SSLMODE": "verify-ca"})
    assert result.returncode != 0
    assert "POSTGRES_SSLROOTCERT" in result.stderr


def test_require_is_available_for_private_network_databases():
    # Encrypts without authenticating the server; only defensible off the public internet.
    result = database_sslmode({"POSTGRES_SSLMODE": "require"})
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["require", "<unset>"]


@pytest.mark.parametrize("mode", ["prefer", "allow", "disable"])
def test_modes_permitting_an_unencrypted_connection_are_refused(mode):
    result = database_sslmode({"POSTGRES_SSLMODE": mode})
    assert result.returncode != 0
    assert "POSTGRES_SSLMODE" in result.stderr


def test_an_empty_sslmode_falls_back_to_the_secure_default():
    result = database_sslmode({"POSTGRES_SSLMODE": ""})
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["verify-full", "<unset>"]


def media_settings(extra_environment=None, removed=()):
    """Load production settings and report how media is addressed and stored."""
    environment = os.environ.copy()
    environment.update(
        DJANGO_SECRET_KEY="production-settings-test-" + "0123456789abcdef" * 4,
        DJANGO_ALLOWED_HOSTS="demo.example.com",
        DJANGO_SITE_URL="https://demo.example.com",
        DJANGO_MEDIA_ORIGIN="https://media.example.net",
        DJANGO_TRUSTED_PROXY_NETWORKS="",
        DJANGO_CSRF_TRUSTED_ORIGINS="https://demo.example.com",
        DJANGO_TRUST_PROXY_HTTPS="false",
        DJANGO_HSTS_SECONDS="0",
    )
    environment.pop("DJANGO_SERVE_MEDIA", None)
    for name in ("MEDIA_BUCKET_NAME", "MEDIA_BUCKET_ENDPOINT"):
        environment.pop(name, None)
    environment.update(extra_environment or {})
    for name in removed:
        environment.pop(name, None)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import config.settings.production as s; "
            "print(s.MEDIA_URL, s.STORAGES['default']['BACKEND'], "
            "','.join(s.CONTENT_SECURITY_POLICY['DIRECTIVES']['img-src']))",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_media_is_addressed_on_a_separate_origin_by_default():
    result = media_settings()
    assert result.returncode == 0, result.stderr
    url, backend, img_src = result.stdout.split()
    assert url == "https://media.example.net/"
    assert backend.endswith("FileSystemStorage")
    assert img_src == "'self',https://media.example.net"


def test_a_separate_media_origin_is_required_unless_serving_media_is_requested():
    assert media_settings(removed=("DJANGO_MEDIA_ORIGIN",)).returncode != 0
    result = media_settings({"DJANGO_SERVE_MEDIA": "true"}, removed=("DJANGO_MEDIA_ORIGIN",))
    assert result.returncode == 0, result.stderr


def test_serving_media_keeps_it_same_origin_without_widening_the_image_policy():
    result = media_settings({"DJANGO_SERVE_MEDIA": "true"})
    assert result.returncode == 0, result.stderr
    url, backend, img_src = result.stdout.split()
    assert url == "/media/"
    assert backend.endswith("FileSystemStorage")
    assert img_src == "'self'"


def test_serving_media_locally_ignores_bucket_configuration():
    result = media_settings(
        {
            "DJANGO_SERVE_MEDIA": "true",
            "MEDIA_BUCKET_NAME": "should-be-ignored",
            "MEDIA_BUCKET_ENDPOINT": "https://buckets.example.net",
        }
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.split()[1].endswith("FileSystemStorage")
