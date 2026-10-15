from urllib.parse import urljoin

from django.conf import settings
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse


def site(request: HttpRequest) -> dict[str, object]:
    routes = (
        ("New in", "catalog:new", ""),
        ("Women", "catalog:women", ""),
        ("Men", "catalog:men", ""),
        ("Accessories", "catalog:accessories", ""),
        ("Collections", "catalog:collections", ""),
    )
    return {
        "brand_name": "MAISON ÉLAN",
        "currency_code": settings.CURRENCY_CODE,
        "canonical_url": f"{settings.SITE_URL}{request.path}",
        "site_origin": settings.SITE_URL,
        "social_image": urljoin(settings.SITE_URL, static("images/editorial/hero-1280.webp")),
        "private_page": request.resolver_match is not None
        and request.resolver_match.namespace in {"cart", "checkout", "marketing", "admin"},
        "navigation": [
            {
                "label": label,
                "url": reverse(route) + fragment,
                "current": request.path == reverse(route) and not fragment,
            }
            for label, route, fragment in routes
        ],
    }
