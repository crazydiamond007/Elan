"""Small, strict environment readers; secrets are never included in errors."""

import os
from ipaddress import ip_network
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"Set the required environment variable {name}.")
    return value


def boolean(name: str, *, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean.")


def integer(name: str, *, default: int, minimum: int = 0, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be an integer.") from None
    if not minimum <= value <= maximum:
        raise ImproperlyConfigured(f"{name} must be between {minimum} and {maximum}.")
    return value


def comma_list(name: str, *, mandatory: bool = False) -> list[str]:
    value = required(name) if mandatory else os.environ.get(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def https_origin(value: str, *, name: str) -> str:
    """Require an HTTPS origin without wildcards, credentials, paths or query strings."""
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ImproperlyConfigured(f"{name} must be a valid HTTPS origin.") from None
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or "*" in parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or (port is not None and port < 1)
    ):
        raise ImproperlyConfigured(f"{name} must be an HTTPS origin without a path.")
    return value.rstrip("/")


def proxy_networks(name):
    results = []
    for value in comma_list(name):
        try:
            network = ip_network(value, strict=True)
        except ValueError:
            raise ImproperlyConfigured(f"{name} must contain explicit IP networks.") from None
        if network.prefixlen == 0:
            raise ImproperlyConfigured(f"{name} must not trust the entire internet.")
        results.append(str(network))
    return results
