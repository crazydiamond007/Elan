import os
import re

from django.conf import settings

import pytest
from django.core.exceptions import SuspiciousFileOperation
from django.test import override_settings

from apps.core.templatetags.metadata import stylesheet_url
from apps.core.views import review_media


def test_development_stylesheet_url_changes_after_a_rebuild(settings, tmp_path):
    settings.DEBUG = True
    settings.STATICFILES_DIRS = [tmp_path]
    stylesheet = tmp_path / "search.css"
    stylesheet.write_text("dialog { height: auto; }")
    first = stylesheet_url("search.css")
    assert first.startswith("/static/search.css?v=")
    assert stylesheet_url("search.css") == first
    timestamp = stylesheet.stat().st_mtime_ns
    os.utime(stylesheet, ns=(timestamp, timestamp + 1_000_000_000))
    assert stylesheet_url("search.css") != first


@override_settings(DEBUG=False)
def test_non_debug_stylesheet_url_uses_configured_static_storage():
    assert stylesheet_url("css/app.css") == "/static/css/app.css"


# The generated-media route is loopback-only under LOCAL_REVIEW, but DJANGO_SERVE_MEDIA also
# enables it for single-origin deployments, so it serves public traffic and is tested as such.

GENERATED_NAME = "7/0123456789abcdef0123456789abcdef.webp"
MEDIA_PATTERN = re.compile(r"^media/products/(?P<path>[0-9]+/[a-f0-9]{32}\.webp)$")


@pytest.fixture
def generated_media(settings, tmp_path):
    products = tmp_path / "products" / "7"
    products.mkdir(parents=True)
    (products / "0123456789abcdef0123456789abcdef.webp").write_bytes(b"RIFF....WEBPVP8 ")
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def test_generated_media_is_served_with_immutable_caching(rf, generated_media):
    response = review_media(rf.get(f"/media/products/{GENERATED_NAME}"), GENERATED_NAME)
    assert response.status_code == 200
    cache_control = response.headers["Cache-Control"]
    assert "immutable" in cache_control and "max-age=31536000" in cache_control


def test_generated_media_rejects_unsafe_methods(rf, generated_media):
    response = review_media(rf.post(f"/media/products/{GENERATED_NAME}"), GENERATED_NAME)
    assert response.status_code == 405


def test_generated_media_does_not_escape_the_products_directory(rf, generated_media):
    (generated_media / "secret.webp").write_bytes(b"not for serving")
    with pytest.raises(SuspiciousFileOperation):
        review_media(rf.get("/media/products/x"), "../secret.webp")


@pytest.mark.parametrize(
    "path",
    [
        "media/products/../../etc/passwd",
        "media/products/7/0123456789abcdef0123456789abcdef.webp.php",
        "media/products/7/UPPERCASE789abcdef0123456789abcde.webp",
        "media/products/7/short.webp",
        "media/products/7/0123456789abcdef0123456789abcdef.jpg",
        "media/originals/7/0123456789abcdef0123456789abcdef.webp",
    ],
)
def test_media_route_matches_only_generated_product_names(path):
    assert MEDIA_PATTERN.match(path) is None


def test_media_route_matches_a_generated_product_name():
    assert MEDIA_PATTERN.match(f"media/products/{GENERATED_NAME}")


# Browsers request /favicon.ico whatever the document declares, so the path is routed rather than
# left to record a 404 on every visit.


@pytest.mark.django_db
def test_favicon_ico_points_at_the_declared_icon(client):
    response = client.get("/favicon.ico")
    assert response.status_code == 302
    assert response.headers["Location"].endswith(".svg")
    assert "images/favicon" in response.headers["Location"]


@pytest.mark.django_db
def test_favicon_ico_is_not_permanent(client):
    # The target carries a content hash, so a permanent redirect would be cached against a
    # filename the next build replaces.
    assert client.get("/favicon.ico").status_code != 301


@pytest.mark.django_db
@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_favicon_ico_rejects_unsafe_methods(client, method):
    assert getattr(client, method)("/favicon.ico").status_code == 405


def test_the_icon_is_legible_at_tab_size():
    source = (settings.BASE_DIR / "static" / "images" / "favicon.svg").read_text()
    # A 48-unit viewBox renders at 16px, dividing every unit by three; a hairline stroke vanishes.
    width = float(re.search(r'stroke-width="([0-9.]+)"', source).group(1))
    assert width / 3 >= 1.0, "stroke would render thinner than a pixel in a browser tab"
    # Drawn on the brand's dark tone so it survives a light browser chrome.
    assert 'fill="#222222"' in source
