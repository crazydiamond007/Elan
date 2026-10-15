from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import Color, Product, Variant

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("catalog_data")]


def slugs(response):
    return [piece.slug for piece in response.context["page_obj"]]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("coat", ["sculpted-coat"]),
        ("KNIT", ["fine-wool-knit"]),
        ("ME-001-XS", ["sculpted-coat"]),
        ("not-existing", []),
    ],
)
def test_search_names_descriptions_and_active_skus(client, query, expected):
    response = client.get(reverse("catalog:all"), {"q": query})
    assert response.status_code == 200
    assert slugs(response) == expected


def test_filters_match_options_and_price_on_one_variant(client):
    product = Product.objects.get(slug="sculpted-coat")
    source = product.variants.get(size__slug="m")
    slate = Color.objects.create(slug="slate", name="Slate")
    Variant.objects.create(
        product=product, sku="ME-SLATE-M", color=slate, size=source.size, price="25.50", stock=1
    )
    for filters in (
        {"color": "charcoal", "max_price": "100"},
        {"size": "xs", "max_price": "100"},
        {"q": "ME-001", "color": "slate"},
    ):
        assert "sculpted-coat" not in slugs(client.get("/shop/", filters))
    response = client.get("/shop/", {"color": "slate", "size": "m", "max_price": "100"})
    assert slugs(response) == ["sculpted-coat"]
    assert response.context["page_obj"][0].price == Decimal("25.50")
    assert "€25.50" in response.content.decode()


def test_sale_filters_must_match_a_discounted_variant(client):
    product = Product.objects.get(slug="sculpted-coat")
    source = product.variants.get(size__slug="m")
    slate = Color.objects.create(slug="slate", name="Slate")
    Variant.objects.create(
        product=product,
        sku="SALE-SLATE-M",
        color=slate,
        size=source.size,
        price="25.00",
        compare_at_price="30.00",
        stock=1,
    )
    assert "sculpted-coat" not in slugs(client.get("/shop/sale/", {"color": "charcoal"}))
    sale = client.get("/shop/sale/", {"color": "slate"})
    assert slugs(sale) == ["sculpted-coat"]
    assert sale.context["page_obj"][0].price == Decimal("25.00")


def test_price_range_categories_sizes_colors_and_sorting(client):
    assert slugs(client.get("/shop/", {"category": "accessories"})) == ["everyday-tote"]
    assert slugs(client.get("/shop/", {"min_price": "145", "max_price": "160"})) == [
        "pleated-trouser",
        "fine-wool-knit",
    ]
    assert slugs(client.get("/shop/", {"color": "ivory", "size": "m"})) == ["fine-wool-knit"]
    assert slugs(client.get("/shop/", {"size": "one-size"})) == ["everyday-tote"]
    assert slugs(client.get("/shop/", {"sort": "price-asc"})) == [
        "fine-wool-knit",
        "pleated-trouser",
        "everyday-tote",
        "sculpted-coat",
    ]
    assert slugs(client.get("/shop/", {"sort": "price-desc"})) == [
        "sculpted-coat",
        "everyday-tote",
        "pleated-trouser",
        "fine-wool-knit",
    ]


@pytest.mark.parametrize(
    "parameters",
    [
        {"q": "x" * 81},
        {"min_price": "NaN"},
        {"max_price": "Infinity"},
        {"min_price": "-1"},
        {"min_price": "12.345"},
        {"max_price": "999999999999"},
        {"min_price": "200", "max_price": "10"},
        {"sort": "price;DROP TABLE"},
        {"color": "unknown"},
        {"size": "unknown"},
        {"category": "unknown"},
    ],
)
def test_bad_search_parameters_return_form_errors_without_unfiltered_results(client, parameters):
    response = client.get("/shop/", parameters)
    assert response.status_code == 400
    assert b"Please check your filters" in response.content
    assert not slugs(response)


def test_duplicate_filter_parameters_are_rejected(client):
    assert client.get("/shop/?max_price=10&max_price=500").status_code == 400


def test_search_is_escaped_and_does_not_interpret_sql(client):
    response = client.get("/shop/", {"q": "<script>alert(1)</script>"})
    assert b"<script>alert(1)" not in response.content
    assert b"&lt;script&gt;" in response.content
    assert not slugs(client.get("/shop/", {"q": "' OR 1=1 --"}))


def test_pagination_keeps_filters_and_sort(client):
    product = Product.objects.get(slug="sculpted-coat")
    variant = product.variants.first()
    for index in range(13):
        clone = Product.objects.create(
            name=f"Extra coat {index}",
            slug=f"extra-coat-{index}",
            description="Test only",
            category=product.category,
            status="published",
            published_at=product.published_at,
        )
        Variant.objects.create(
            product=clone,
            sku=f"EXTRA-{index}",
            size=variant.size,
            color=variant.color,
            price="40.00",
            stock=1,
        )
    response = client.get("/shop/", {"q": "Extra coat", "sort": "price-asc"})
    assert len(response.context["page_obj"]) == 12
    assert "q=Extra+coat&amp;sort=price-asc&amp;page=2" in response.content.decode()
    assert (
        len(
            client.get("/shop/", {"q": "Extra coat", "sort": "price-asc", "page": "2"}).context[
                "page_obj"
            ]
        )
        == 1
    )
