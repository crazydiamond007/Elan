"""Temporary HTTP preview on a trusted private LAN; never use for public hosting."""

from ipaddress import IPv4Address, IPv4Network

from django.core.exceptions import ImproperlyConfigured

from config.env import integer, required

from .review import *  # noqa: F403

try:
    preview_host = IPv4Address(required("LAN_PREVIEW_HOST"))
except ValueError:
    raise ImproperlyConfigured("LAN_PREVIEW_HOST must be a private IPv4 address.") from None
if not any(
    preview_host in IPv4Network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
):
    raise ImproperlyConfigured("LAN_PREVIEW_HOST must be a private LAN IPv4 address.")

preview_port = integer("LAN_PREVIEW_PORT", default=8001, minimum=1024, maximum=65535)
ALLOWED_HOSTS = ["localhost", "127.0.0.1", str(preview_host)]
SITE_URL = f"http://{preview_host}:{preview_port}"
LAN_PREVIEW = True
