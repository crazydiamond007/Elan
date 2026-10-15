import pytest
from django.db import DatabaseError

pytestmark = pytest.mark.django_db


def test_health_is_database_free_and_not_cached(client, django_assert_num_queries):
    with django_assert_num_queries(0):
        response = client.get("/healthz/")
    assert response.json() == {"status": "ok"}
    assert "no-store" in response["Cache-Control"]


def test_readiness_checks_database_without_disclosing_details(client, monkeypatch):
    from apps.core import views

    assert client.get("/readyz/").json() == {"status": "ready"}
    monkeypatch.setattr(
        views.connection,
        "cursor",
        lambda: (_ for _ in ()).throw(DatabaseError("private-password-marker")),
    )
    response = client.get("/readyz/")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert b"private-password-marker" not in response.content
