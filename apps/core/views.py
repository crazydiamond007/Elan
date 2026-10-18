from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.cache import patch_cache_control
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe
from django.views.static import serve

from apps.catalog.models import Collection, Product

from .sitemaps import SITEMAPS


@require_safe
def home(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "core/home.html",
        {
            "arrivals": Product.objects.public().for_display()[:4],
            "favourites": Product.objects.public().for_display().filter(is_signature=True)[:3],
            "campaign": Collection.objects.for_display()
            .filter(is_active=True, is_featured=True, cover_is_public=True)
            .order_by("position", "pk")
            .first(),
        },
    )


@require_safe
def collection_preview(request: HttpRequest, department: str = "") -> HttpResponse:
    return redirect(f"catalog:{department or 'all'}", permanent=True)


@require_safe
def story(request: HttpRequest) -> HttpResponse:
    return render(request, "core/story.html")


@require_safe
def care(request: HttpRequest) -> HttpResponse:
    return render(request, "core/care.html")


@require_safe
def size_guide(request: HttpRequest) -> HttpResponse:
    return render(request, "core/size_guide.html")


@require_safe
def demo_information(request: HttpRequest) -> HttpResponse:
    return render(request, "core/demo_information.html")


@require_safe
def robots(request: HttpRequest) -> HttpResponse:
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain; charset=utf-8")


@require_safe
def sitemap(request):
    parsed = urlsplit(settings.SITE_URL)
    site = SimpleNamespace(domain=parsed.netloc, name="MAISON ÉLAN")
    entries = [
        entry
        for sitemap_type in SITEMAPS.values()
        for entry in sitemap_type().get_urls(site=site, protocol=parsed.scheme)
    ]
    return render(request, "core/sitemap.xml", {"entries": entries}, content_type="application/xml")


@never_cache
@require_safe
def health(request):
    return JsonResponse({"status": "ok"})


@never_cache
@require_safe
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})


@require_safe
def review_media(request, path):
    """Loopback review equivalent of the immutable, generated-WebP media policy."""
    response = serve(request, path, document_root=settings.MEDIA_ROOT / "products")
    patch_cache_control(response, public=True, max_age=31536000, immutable=True)
    return response


def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:
    return render(request, "errors/csrf.html", status=403)


def bad_request(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "errors/400.html", status=400)


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "errors/403.html", status=403)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "errors/404.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    # Error rendering must not read an unavailable database just to show a bag count.
    request._skip_cart_badge = True
    return render(request, "errors/500.html", status=500)
