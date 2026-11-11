import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

# The command runs on every container start, so each test asserts a property that must hold on a
# repeat run, not only the first one.

STRONG_PASSWORD = "quiet-limestone-courtyard-4471"


def bootstrap(**options):
    call_command("bootstrap_deployment", skip_seed=True, **options)


@pytest.mark.django_db
def test_an_administrator_is_created_from_the_environment(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "curator")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", STRONG_PASSWORD)
    monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "curator@example.com")
    bootstrap()
    user = get_user_model().objects.get(username="curator")
    assert user.is_superuser and user.is_staff
    assert user.email == "curator@example.com"
    assert user.check_password(STRONG_PASSWORD)


@pytest.mark.django_db
def test_repeating_the_bootstrap_does_not_reset_an_existing_password(monkeypatch):
    users = get_user_model()
    users.objects.create_superuser(username="curator", email="", password=STRONG_PASSWORD)
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "curator")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "a-different-password-entirely-9931")
    bootstrap()
    # A password changed through the admin must survive the next restart.
    assert users.objects.get(username="curator").check_password(STRONG_PASSWORD)
    assert users.objects.filter(username="curator").count() == 1


@pytest.mark.django_db
def test_a_weak_administrator_password_fails_the_deployment(monkeypatch):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "curator")
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "password")
    with pytest.raises(CommandError, match="DJANGO_SUPERUSER_PASSWORD"):
        bootstrap()
    assert not get_user_model().objects.filter(username="curator").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("username", "password"),
    [("", STRONG_PASSWORD), ("curator", ""), ("", "")],
)
def test_an_incomplete_administrator_definition_creates_nobody(monkeypatch, username, password):
    monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", username)
    monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", password)
    bootstrap()
    assert not get_user_model().objects.exists()
