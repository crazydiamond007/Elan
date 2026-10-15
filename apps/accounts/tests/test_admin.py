import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from apps.accounts.admin import UserAdmin

pytestmark = pytest.mark.django_db


def test_custom_user_and_password_hashing():
    user = get_user_model().objects.create_user("editor", password="Example-password-42")
    assert user._meta.label == "accounts.User"
    assert user.check_password("Example-password-42")
    assert user.password != "Example-password-42"
    assert not user.is_staff
    assert not user.is_superuser


def test_anonymous_admin_redirects_to_login(client):
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


@pytest.mark.parametrize(("is_staff", "is_active"), [(False, True), (True, False)])
def test_nonstaff_and_inactive_users_cannot_access_admin(client, is_staff, is_active):
    user = get_user_model().objects.create_user("visitor", is_staff=is_staff, is_active=is_active)
    client.force_login(user)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


def test_staff_requires_model_permissions(client):
    user = get_user_model().objects.create_user("editor", is_staff=True)
    client.force_login(user)
    response = client.get(reverse("admin:accounts_user_changelist"))
    assert response.status_code == 403


def test_view_permission_does_not_grant_change_permission(client):
    user = get_user_model().objects.create_user("reader", is_staff=True)
    user.user_permissions.add(Permission.objects.get(codename="view_user"))
    client.force_login(user)
    assert client.get(reverse("admin:accounts_user_changelist")).status_code == 200
    assert client.get(reverse("admin:accounts_user_add")).status_code == 403


def test_admin_login_requires_csrf():
    client = Client(enforce_csrf_checks=True)
    response = client.post(reverse("admin:login"), {"username": "unknown", "password": "example"})
    assert response.status_code == 403
    assert b"Your form could not be verified" in response.content


def test_admin_login_and_logout_with_valid_csrf():
    user = get_user_model().objects.create_user(
        "editor", password="Example-password-42", is_staff=True
    )
    client = Client(enforce_csrf_checks=True)
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200
    response = client.post(
        reverse("admin:login"),
        {
            "username": user.username,
            "password": "Example-password-42",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value,
            "next": reverse("admin:index"),
        },
    )
    assert response.status_code == 302
    assert client.get(reverse("admin:index")).status_code == 200
    assert client.cookies["sessionid"]["httponly"]
    assert client.cookies["sessionid"]["samesite"] == "Lax"
    response = client.post(
        reverse("admin:logout"),
        {"csrfmiddlewaretoken": client.cookies["csrftoken"].value},
    )
    assert response.status_code == 200
    assert client.get(reverse("admin:index")).status_code == 302


def test_admin_conditional_style_has_matching_csp_nonce(client, monkeypatch):
    user = get_user_model().objects.create_superuser(
        "administrator", password="Example-password-42"
    )
    client.force_login(user)
    monkeypatch.setattr(UserAdmin, "actions_on_top", False)
    monkeypatch.setattr(UserAdmin, "actions_on_bottom", False)
    response = client.get(reverse("admin:accounts_user_changelist"))
    assert response.status_code == 200
    nonce = response.wsgi_request._csp_nonce
    assert f'<style nonce="{nonce}">' in response.content.decode()
    assert f"'nonce-{nonce}'" in response["Content-Security-Policy"]
    assert "'unsafe-inline'" not in response["Content-Security-Policy"]


def test_admin_login_attempts_are_rate_limited_without_echoing_credentials(client):
    for _ in range(10):
        assert (
            client.post(
                reverse("admin:login"), {"username": "unknown", "password": "fake-test-password"}
            ).status_code
            == 200
        )
    response = client.post(
        reverse("admin:login"), {"username": "unknown", "password": "private-password-marker"}
    )
    assert response.status_code == 429
    assert response["Retry-After"] == "600"
    assert b"private-password-marker" not in response.content
    assert "no-store" in response["Cache-Control"]
