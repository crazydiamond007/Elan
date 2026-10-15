import json
import re
from xml.etree import ElementTree

import pytest
from django.urls import reverse

from apps.catalog.models import Product

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("catalog_data")]


def structured(response):
    block = re.search(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        response.content.decode(),
        re.DOTALL,
    )
    assert block
    return json.loads(block.group(1))


def test_public_metadata_uses_trusted_origins_and_keeps_noindex(client):
    response = client.get("/", {"q": "ignored"})
    body = response.content.decode()
    assert 'property="og:url" content="http://testserver/"' in body
    assert 'property="og:image" content="http://testserver/static/' in body
    assert 'property="og:locale" content="en_GB"' in body
    assert 'name="twitter:card"' in body
    assert structured(response)["@type"] == "WebSite"
    nonce = response.wsgi_request.csp_nonce
    assert f'nonce="{nonce}"' in body
    assert f"'nonce-{nonce}'" in response["Content-Security-Policy"]
    assert "noindex" in response["X-Robots-Tag"]
    assert "private" in response["Cache-Control"]


def test_product_json_is_escaped_and_does_not_imply_real_offers(client):
    marker = '</script><script>alert("unsafe")</script>&'
    Product.objects.filter(slug="sculpted-coat").update(description=marker)
    response = client.get("/products/sculpted-coat/")
    data = structured(response)
    assert data["@type"] == "Product"
    assert marker in data["description"]
    assert "offers" not in data and "aggregateRating" not in data
    assert data["image"].startswith("http://testserver/media/")
    assert marker not in response.content.decode()
    assert r"\u003C/script\u003E" in response.content.decode()


@pytest.mark.parametrize("route", ["/bag/", "/checkout/", "/newsletter/", "/missing/"])
def test_private_or_error_pages_do_not_have_share_metadata(client, route):
    body = client.get(route).content.decode()
    assert 'property="og:url"' not in body
    assert 'rel="canonical"' not in body
    assert 'type="application/ld+json"' not in body


def test_sitemap_contains_only_public_pages_using_the_configured_origin(client):
    Product.objects.filter(slug="sculpted-coat").update(status="draft")
    response = client.get(reverse("core:sitemap"), HTTP_HOST="localhost")
    assert response.status_code == 200
    root = ElementTree.fromstring(response.content)
    urls = [node.text for node in root.findall("{*}url/{*}loc")]
    assert "http://testserver/products/fine-wool-knit/" in urls
    assert not any("sculpted-coat" in url for url in urls)
    assert not any(
        path in url for url in urls for path in ("/admin/", "/bag/", "/checkout/", "/newsletter/")
    )
    assert all(url.startswith("http://testserver/") for url in urls)
    assert "noindex" in response["X-Robots-Tag"]
    assert b"Sitemap" not in client.get(reverse("core:robots")).content
