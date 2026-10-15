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
