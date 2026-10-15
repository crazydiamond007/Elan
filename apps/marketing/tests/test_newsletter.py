import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from apps.marketing.models import DemoSignup

pytestmark = pytest.mark.django_db


def test_fictional_signup_is_normalized_and_duplicate_safe_without_sending_email(client):
    for email in ("Guest@Example.com", "guest@example.com"):
        response = client.post(reverse("marketing:newsletter"), {"email": email}, follow=True)
        assert response.status_code == 200
        assert b"Your demo signup was saved locally" in response.content
    assert DemoSignup.objects.count() == 1
    assert DemoSignup.objects.get().email == "guest@example.com"
    assert not mail.outbox
    assert "no-store" in response["Cache-Control"]


@pytest.mark.parametrize(
    "email", ["not-email", "", "real@gmail.com", "real@company.com", "x" * 260 + "@example.com"]
)
def test_invalid_or_real_addresses_are_rejected(client, email):
    response = client.post(reverse("marketing:newsletter"), {"email": email})
    assert response.status_code == 400
    assert b"Please check the form" in response.content
    assert not DemoSignup.objects.exists()


@pytest.mark.parametrize(
    "email",
    ["visitor@example.net", "visitor@example.org", "visitor@maison.test", "visitor@maison.invalid"],
)
def test_reserved_domains_are_accepted(client, email):
    assert client.post(reverse("marketing:newsletter"), {"email": email}).status_code == 302
    assert DemoSignup.objects.filter(email=email).exists()


def test_model_validation_rejects_genuine_addresses():
    with pytest.raises(ValidationError):
        DemoSignup(email="person@gmail.com").full_clean()


def test_newsletter_requires_csrf_and_rejects_put():
    assert (
        Client(enforce_csrf_checks=True)
        .post(reverse("marketing:newsletter"), {"email": "guest@example.com"})
        .status_code
        == 403
    )
    assert Client().put(reverse("marketing:newsletter"), {}).status_code == 405


def test_rate_limit_uses_remote_address_not_forwarded_header(client):
    for index in range(5):
        assert (
            client.post(
                reverse("marketing:newsletter"),
                {"email": f"test-{index}@example.com"},
                HTTP_X_FORWARDED_FOR=f"10.0.0.{index}",
            ).status_code
            == 302
        )
    response = client.post(
        reverse("marketing:newsletter"),
        {"email": "sixth@example.com"},
        HTTP_X_FORWARDED_FOR="1.2.3.4",
    )
    assert response.status_code == 429
    assert response["Retry-After"] == "600"
    assert DemoSignup.objects.count() == 5
