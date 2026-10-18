import pytest
from django.template import Context, Template
from django.test import RequestFactory
from django.urls import resolve, reverse
from django.utils.functional import SimpleLazyObject

from apps.core import views

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "name",
    [
        "core:home",
        "core:demo_information",
        "catalog:all",
        "catalog:women",
        "catalog:men",
        "catalog:accessories",
        "core:story",
        "core:care",
        "core:size_guide",
    ],
)
def test_public_pages_have_demo_disclosure_and_accessible_shell(client, name):
    response = client.get(reverse(name))
    assert response.status_code == 200
    content = response.content.decode()
    assert "Demonstration website" in content
    assert "No real purchases" in content
    assert 'href="#main-content"' in content
    assert 'id="main-content"' in content
    assert '<html lang="en-GB">' in content
    assert 'name="robots" content="noindex, nofollow, noarchive"' in content
    assert response["X-Robots-Tag"] == "noindex, nofollow, noarchive"


def test_canonical_omits_query_parameters(client):
    response = client.get(reverse("core:home"), {"q": "example"})
    assert '<link rel="canonical" href="http://testserver/">' in response.content.decode()


def test_robots_disallows_all_crawlers(client):
    response = client.get(reverse("core:robots"))
    assert response.content == b"User-agent: *\nDisallow: /\n"
    assert response["Content-Type"].startswith("text/plain")


def test_home_rejects_state_changing_requests(client):
    assert client.post(reverse("core:home")).status_code == 405


def test_head_request_succeeds_without_a_body(client):
    response = client.head(reverse("core:home"))
    assert response.status_code == 200
    assert response.content == b""


def test_page_has_strict_security_headers(client):
    response = client.get(reverse("core:home"))
    policy = response["Content-Security-Policy"]
    for directive in (
        "default-src 'none'",
        "script-src 'self'",
        "script-src-attr 'none'",
        "form-action 'self'",
        "frame-ancestors 'none'",
        "object-src 'none'",
    ):
        assert directive in policy
    assert "'unsafe-inline'" not in policy
    assert "'unsafe-eval'" not in policy
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_unknown_path_returns_safe_error_page(client):
    response = client.get("/missing-private-path/")
    assert response.status_code == 404
    assert b"Page not found" in response.content
    assert b"missing-private-path" not in response.content
    assert "Content-Security-Policy" in response
    assert "noindex" in response["X-Robots-Tag"]


def test_untrusted_host_is_rejected(client):
    assert client.get("/", HTTP_HOST="untrusted.example").status_code == 400


def test_https_redirect_retains_demo_noindex_header(client, settings):
    settings.SECURE_SSL_REDIRECT = True
    response = client.get("/")
    assert response.status_code == 301
    assert response.url == "https://testserver/"
    assert "noindex" in response["X-Robots-Tag"]


@pytest.mark.parametrize(
    ("view", "status", "message"),
    [
        (views.bad_request, 400, "Unable to open this page"),
        (views.permission_denied, 403, "Access unavailable"),
        (views.page_not_found, 404, "Page not found"),
    ],
)
def test_error_pages_do_not_disclose_exception_details(view, status, message):
    response = view(RequestFactory().get("/"), Exception("private-diagnostic-marker"))
    assert response.status_code == status
    assert message in response.content.decode()
    assert b"private-diagnostic-marker" not in response.content


@pytest.mark.django_db
def test_server_error_renders_without_database_queries(django_assert_num_queries):
    request = RequestFactory().get("/")
    request.resolver_match = resolve("/")
    request.session = SimpleLazyObject(
        lambda: pytest.fail("Error rendering must not load the session for the bag badge.")
    )
    with django_assert_num_queries(0):
        response = views.server_error(request)
    assert response.status_code == 500
    assert b"Temporarily unavailable" in response.content


def test_template_content_is_autoescaped():
    template = Template("{% extends 'base.html' %}{% block content %}{{ value }}{% endblock %}")
    content = template.render(Context({"value": "<script>alert('example')</script>"}))
    assert "<script>" not in content
    assert "&lt;script&gt;" in content
