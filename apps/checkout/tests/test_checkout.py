from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import pytest
from django.db import close_old_connections
from django.test import Client
from django.urls import reverse

from apps.catalog.models import Product, Variant
from apps.checkout.models import DemoReceipt

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("catalog_data")]


def prepare(client):
    client.post(
        reverse("cart:add"),
        {"product_slug": "sculpted-coat", "color": "charcoal", "size": "m", "quantity": 2},
    )
    response = client.get(reverse("checkout:review"))
    return response.context["form"].initial["token"]


def test_checkout_is_a_session_bound_simulation_with_accurate_snapshots(client):
    token = prepare(client)
    before = list(Variant.objects.values_list("pk", "stock"))
    response = client.post(
        reverse("checkout:review"),
        {"token": token, "acknowledge": "on", "price": "0.01", "address": "Ignored"},
    )
    assert response.status_code == 302
    receipt = DemoReceipt.objects.get()
    assert receipt.subtotal == Decimal("640.00")
    assert receipt.lines[0]["unit_price"] == "320.00"
    assert receipt.lines[0]["quantity"] == 2
    assert "address" not in receipt.lines[0]
    assert client.session["cart"] == {}
    assert list(Variant.objects.values_list("pk", "stock")) == before
    confirmation = client.get(response.url)
    assert confirmation.status_code == 200
    assert b"No payment was taken" in confirmation.content
    assert b"nothing will be dispatched" in confirmation.content
    assert "€640.00" in confirmation.content.decode()
    assert "no-store" in confirmation["Cache-Control"]
    assert Client().get(response.url).status_code == 404


def test_replayed_submission_is_idempotent_and_does_not_clear_a_new_bag(client):
    token = prepare(client)
    first = client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
    client.post(
        reverse("cart:add"),
        {"product_slug": "everyday-tote", "color": "black", "size": "one-size", "quantity": 1},
    )
    new_cart = client.session["cart"]
    second = client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
    assert second.url == first.url
    assert DemoReceipt.objects.count() == 1
    assert client.session["cart"] == new_cart


@pytest.mark.parametrize("changes", [{"stock": 1}, {"is_active": False}])
def test_checkout_rechecks_variant_availability(client, changes):
    token = prepare(client)
    Variant.objects.filter(product__slug="sculpted-coat", size__slug="m").update(**changes)
    response = client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
    assert response.status_code == 409
    assert not DemoReceipt.objects.exists()
    assert client.session["cart"]


def test_checkout_rechecks_product_publication(client):
    token = prepare(client)
    Product.objects.filter(slug="sculpted-coat").update(status="draft")
    assert (
        client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"}).status_code
        == 409
    )
    assert not DemoReceipt.objects.exists()


def test_changed_price_requires_new_review_and_confirmation(client):
    token = prepare(client)
    Variant.objects.filter(product__slug="sculpted-coat", size__slug="m").update(price="325.25")
    response = client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
    assert response.status_code == 409
    assert b"price or quantity has changed" in response.content
    assert not DemoReceipt.objects.exists()
    refreshed = response.context["form"].initial["token"]
    assert refreshed != token
    assert (
        client.post(
            reverse("checkout:review"), {"token": refreshed, "acknowledge": "on"}
        ).status_code
        == 302
    )
    assert DemoReceipt.objects.get().subtotal == Decimal("650.50")


def test_cart_mutation_invalidates_previously_reviewed_checkout(client):
    token = prepare(client)
    variant = Variant.objects.get(product__slug="sculpted-coat", size__slug="m")
    client.post(reverse("cart:update"), {"variant_id": variant.pk, "quantity": 1})
    response = client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
    assert response.status_code == 409
    assert not DemoReceipt.objects.exists()


@pytest.mark.parametrize(
    "data", [{}, {"token": "bad", "acknowledge": "on"}, {"token": "", "acknowledge": "on"}]
)
def test_invalid_checkout_form_does_not_create_confirmation(client, data):
    token = prepare(client)
    response = client.post(reverse("checkout:review"), {"token": token} | data)
    assert response.status_code == 400
    assert not DemoReceipt.objects.exists()


def test_guessed_token_and_cross_session_replay_are_rejected(client):
    prepare(client)
    assert (
        client.post(
            reverse("checkout:review"), {"token": str(uuid4()), "acknowledge": "on"}
        ).status_code
        == 409
    )
    token = client.get(reverse("checkout:review")).context["form"].initial["token"]
    client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
    other = Client()
    prepare(other)
    assert (
        other.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"}).status_code
        == 409
    )
    assert DemoReceipt.objects.count() == 1


def test_checkout_requires_csrf_and_confirmation_is_read_only():
    client = Client(enforce_csrf_checks=True)
    assert client.post(reverse("checkout:review"), {}).status_code == 403
    assert client.post(reverse("checkout:confirmation", args=[uuid4()]), {}).status_code == 403


def test_empty_checkout_has_no_payment_or_address_form(client):
    response = client.get(reverse("checkout:review"))
    assert response.status_code == 200
    assert b"Your demo bag is empty" in response.content
    assert b'name="address"' not in response.content
    assert b'name="card"' not in response.content
    assert "no-store" in response["Cache-Control"]


def test_demo_review_collects_only_token_and_explicit_acknowledgement(client):
    prepare(client)
    form = client.get(reverse("checkout:review")).context["form"]
    assert set(form.fields) == {"token", "acknowledge"}


def test_checkout_rate_limit_returns_429(client):
    token = prepare(client)
    for _ in range(10):
        client.post(reverse("checkout:review"), {"token": token})
    response = client.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
    assert response.status_code == 429
    assert response["Retry-After"] == "600"
    assert not DemoReceipt.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_simultaneous_duplicate_submissions_create_one_receipt(client):
    token = prepare(client)
    session_id = client.cookies["sessionid"].value

    def submit(_):
        close_old_connections()
        try:
            other = Client()
            other.cookies["sessionid"] = session_id
            response = other.post(reverse("checkout:review"), {"token": token, "acknowledge": "on"})
            return response.status_code, response.url
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert results[0] == results[1]
    assert results[0][0] == 302
    assert DemoReceipt.objects.count() == 1
