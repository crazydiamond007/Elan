from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from django.db import close_old_connections
from django.test import Client
from django.urls import reverse

from apps.cart import services
from apps.catalog.models import Product, Variant

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("catalog_data")]


def add(client, **changes):
    data = {"product_slug": "sculpted-coat", "color": "charcoal", "size": "m", "quantity": "1"}
    return client.post(reverse("cart:add"), data | changes)


def test_add_update_remove_and_decimal_totals(client):
    assert add(client, quantity="2", price="0.01").status_code == 302
    variant = Variant.objects.get(product__slug="sculpted-coat", size__slug="m")
    assert client.session["cart"] == {str(variant.pk): 2}
    response = client.get(reverse("cart:bag"))
    assert response.context["bag"].subtotal == Decimal("640.00")
    assert "€640.00" in response.content.decode()
    assert add(client).status_code == 302
    assert client.session["cart"][str(variant.pk)] == 3
    assert (
        client.post(reverse("cart:update"), {"variant_id": variant.pk, "quantity": 1}).status_code
        == 302
    )
    assert client.get(reverse("cart:bag")).context["bag"].subtotal == Decimal("320.00")
    assert client.post(reverse("cart:remove"), {"variant_id": variant.pk}).status_code == 302
    assert client.session["cart"] == {}
    assert b"Your demo bag is empty" in client.get(reverse("cart:bag")).content


@pytest.mark.parametrize("quantity", ["0", "-1", "11", "1.5", "NaN", "abc", "99999999999999999999"])
def test_invalid_quantities_never_enter_cart(client, quantity):
    assert add(client, quantity=quantity).status_code == 400
    assert not client.session.get("cart")


def test_stock_and_publication_are_validated_on_add_and_update(client):
    assert add(client, size="l").status_code == 409
    assert add(client, quantity="7").status_code == 409
    assert add(client).status_code == 302
    variant = Variant.objects.get(product__slug="sculpted-coat", size__slug="m")
    variant.is_active = False
    variant.save()
    assert add(client).status_code == 409
    assert (
        client.post(reverse("cart:update"), {"variant_id": variant.pk, "quantity": 2}).status_code
        == 409
    )
    Product.objects.filter(slug="fine-wool-knit").update(status="draft")
    assert add(client, product_slug="fine-wool-knit", color="ivory").status_code == 409


def test_stock_changes_and_hidden_products_block_checkout_without_disclosing_draft_data(client):
    add(client, quantity=2)
    variant = Variant.objects.get(product__slug="sculpted-coat", size__slug="m")
    variant.stock = 1
    variant.save()
    response = client.get(reverse("cart:bag"))
    assert not response.context["bag"].valid
    assert b"available stock has changed" in response.content
    variant.product.status = "draft"
    variant.product.save()
    response = client.get(reverse("cart:bag"))
    assert variant.product.name.encode() not in response.content
    assert b"Unavailable piece" in response.content
    assert client.post(reverse("cart:remove"), {"variant_id": variant.pk}).status_code == 302


def test_current_database_prices_are_used_each_time(client):
    add(client)
    Variant.objects.filter(product__slug="sculpted-coat", size__slug="m").update(price="325.25")
    assert client.get(reverse("cart:bag")).context["bag"].subtotal == Decimal("325.25")


def test_added_confirmation_and_header_quantity_follow_the_session(client):
    assert add(client, quantity=2).status_code == 302
    response = client.get(reverse("cart:bag"))
    assert response.context["bag_quantity"] == 2
    assert b"Added to your demo bag: The Sculpted Wool Coat" in response.content
    assert b"Charcoal / M" in response.content
    assert b"Quantity 2" in response.content
    assert client.get("/").context["bag_quantity"] == 2
    assert Client().get("/").context["bag_quantity"] == 0
    session = client.session
    session["cart"] = {"1": True, "bad": 99}
    session.save()
    assert client.get("/").context["bag_quantity"] == 0


def test_update_cannot_add_an_item_not_already_in_the_bag(client):
    variant = Variant.objects.first()
    assert (
        client.post(reverse("cart:update"), {"variant_id": variant.pk, "quantity": 1}).status_code
        == 400
    )


def test_sessions_are_isolated_and_responses_are_private(client):
    add(client)
    second = Client()
    assert not second.get(reverse("cart:bag")).context["bag"].lines
    response = client.get(reverse("cart:bag"))
    assert "no-store" in response["Cache-Control"]
    assert "private" in response["Cache-Control"]
    assert "noindex" in response["X-Robots-Tag"]


@pytest.mark.parametrize("route", ["cart:add", "cart:update", "cart:remove"])
def test_mutations_require_post_and_csrf(route):
    client = Client(enforce_csrf_checks=True)
    assert client.get(reverse(route)).status_code == 405
    assert client.post(reverse(route), {}).status_code == 403


def test_legitimate_csrf_protected_add_works_without_javascript():
    client = Client(enforce_csrf_checks=True)
    client.get("/products/sculpted-coat/")
    assert add(client, csrfmiddlewaretoken=client.cookies["csrftoken"].value).status_code == 302


@pytest.mark.parametrize(
    "raw",
    [
        None,
        [],
        "bad",
        {"-1": 1},
        {"999999999999999999999999": 1},
        {"1": True},
        {"1": "2"},
        {"1": 0},
        {"1": 99},
    ],
)
def test_malformed_session_cart_is_bounded_and_ignored(raw):
    assert not services.snapshot({"cart": raw}).lines


def test_snapshot_queries_do_not_grow_per_line(django_assert_num_queries):
    quantities = {str(variant.pk): 1 for variant in Variant.objects.filter(stock__gt=0)}
    with django_assert_num_queries(2):
        bag = services.snapshot({"cart": quantities})
        assert all(line.photo for line in bag.lines)
        assert bag.valid


def test_cart_rate_limit_returns_429_without_mutation(client):
    for _ in range(60):
        client.post(reverse("cart:remove"), {"variant_id": 1})
    response = add(client)
    assert response.status_code == 429
    assert response["Retry-After"] == "60"
    assert not client.session.get("cart")


def test_quantity_limit_applies_to_repeated_adds_without_changing_existing_cart(client):
    variant = Variant.objects.get(product__slug="sculpted-coat", size__slug="m")
    variant.stock = 20
    variant.save()
    assert add(client, quantity=10).status_code == 302
    assert add(client).status_code == 409
    assert client.session["cart"] == {str(variant.pk): 10}


def test_cart_line_limit_preserves_existing_state():
    variant = Variant.objects.filter(stock__gt=0).first()
    state = {str(services.MAX_ID - index): 1 for index in range(20)}
    session = {"cart": state.copy()}
    with pytest.raises(services.CartError, match="20 different pieces"):
        services.change_quantity(session, variant, 1)
    assert session["cart"] == state


@pytest.mark.django_db(transaction=True)
def test_parallel_adds_in_one_shopping_session_preserve_both_changes(client):
    product_page = client.get("/products/sculpted-coat/")
    assert product_page.status_code == 200
    session_id = client.cookies["sessionid"].value

    def submit(_):
        close_old_connections()
        try:
            other = Client()
            other.cookies["sessionid"] = session_id
            return add(other).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(submit, range(2))) == [302, 302]
    variant = Variant.objects.get(product__slug="sculpted-coat", size__slug="m")
    assert client.session["cart"][str(variant.pk)] == 2
