import os
import subprocess
import sys

import pytest


def lan_configuration(host):
    environment = os.environ.copy()
    environment.update(
        DJANGO_SETTINGS_MODULE="config.settings.lan",
        LAN_PREVIEW_HOST=host,
        LAN_PREVIEW_PORT="8001",
    )
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "import django; django.setup(); "
            "from django.conf import settings; "
            "from django.urls import get_resolver; "
            "assert not settings.DEBUG; "
            "assert '*' not in settings.ALLOWED_HOSTS; "
            "assert settings.SITE_URL.startswith('http://'); "
            "assert 'CompressedManifest' in settings.STORAGES['staticfiles']['BACKEND']; "
            "assert 'admin' not in get_resolver().namespace_dict; "
            "print('LAN configuration validated')",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("host", ["192.168.3.30", "10.0.0.5", "172.22.116.136"])
def test_lan_preview_is_non_debug_and_has_no_admin_routes(host):
    result = lan_configuration(host)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "host",
    ["", "*", "0.0.0.0", "127.0.0.1", "169.254.1.1", "8.8.8.8", "192.0.2.1", "::1"],
)
def test_lan_preview_rejects_non_lan_hosts(host):
    result = lan_configuration(host)
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
