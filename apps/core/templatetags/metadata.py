import json
from functools import lru_cache
from pathlib import Path
from urllib.parse import urljoin

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils.html import json_script
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def stylesheet_url(path):
    """Refresh changed development CSS; deployed assets keep manifest-backed URLs."""
    url = static(path)
    if settings.DEBUG and (source := finders.find(path)):
        return f"{url}?v={Path(source).stat().st_mtime_ns}"
    return url


@lru_cache(maxsize=1)
def editorial_manifest(root):
    return json.loads((Path(root) / "assets/editorial/image-manifest.json").read_text())


@register.simple_tag
def editorial_asset(name):
    files = editorial_manifest(str(settings.BASE_DIR))[name]
    return {"sources": files, "large": files[-1]}


@register.simple_tag(takes_context=True)
def structured_metadata(context):
    """Use Django's JSON encoder/HTML escaping; only the known script type is replaced."""
    if not context.get("request") or not context.get("site_origin"):
        return ""
    origin = context["site_origin"]
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "MAISON ÉLAN",
        "url": origin,
        "description": "Fictional fashion demonstration. No real purchases.",
    }
    if product := context.get("structured_product"):
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product.name,
            "url": urljoin(origin, product.get_absolute_url()),
            "description": "Fictional demo product. No real purchases. " + product.description,
            "category": product.category.name,
            "brand": {"@type": "Brand", "name": "MAISON ÉLAN"},
        }
        if image := context.get("social_image"):
            data["image"] = urljoin(origin, image)
        # Deliberately omit offers, reviews and sales claims for products that are not for sale.
    escaped = json_script(data, "structured-metadata")
    nonce = context["request"].csp_nonce
    # All data was serialized and escaped by json_script, including <, > and &.
    return mark_safe(
        escaped.replace('type="application/json"', f'type="application/ld+json" nonce="{nonce}"')
    )
