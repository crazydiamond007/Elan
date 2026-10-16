from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Category, Collection, Color, Product, ProductImage, Variant
from apps.core.editorial import EXPANDED_PIECES

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("catalog_data")]


@pytest.mark.parametrize(
    "change",
    [
        {"status": "draft"},
        {"published_at": timezone.now() + timedelta(days=1)},
    ],
)
def test_unpublished_products_are_hidden_everywhere(client, change):
    product = Product.objects.get(slug="sculpted-coat")
    Product.objects.filter(pk=product.pk).update(**change)
    for route in ("core:home", "catalog:all", "catalog:women", "catalog:new"):
        assert product.name.encode() not in client.get(reverse(route)).content
    assert client.get(product.get_absolute_url()).status_code == 404


def test_inactive_categories_and_variants_hide_products(client):
    product = Product.objects.get(slug="everyday-tote")
    product.variants.update(is_active=False)
    assert client.get(product.get_absolute_url()).status_code == 404
    Category.objects.filter(slug="clothing").update(is_active=False)
    assert client.get("/shop/category/clothing/").status_code == 404
    assert client.get("/products/fine-wool-knit/").status_code == 404


def test_sold_out_products_stay_visible_with_explicit_unavailable_state(client):
    product = Product.objects.get(slug="everyday-tote")
    product.variants.update(stock=0)
    assert b"Unavailable" in client.get(reverse("catalog:all")).content
    response = client.get(product.get_absolute_url())
    assert response.status_code == 200
    assert b"This size is currently unavailable" in response.content
    assert b"disabled" in response.content


@pytest.mark.parametrize(
    "changes",
    [
        {"price": Decimal("0")},
        {"price": Decimal("-1")},
        {"stock": -1},
        {"compare_at_price": Decimal("1")},
    ],
)
def test_variant_validation_and_database_constraints(changes):
    variant = Variant.objects.first()
    for field, value in changes.items():
        setattr(variant, field, value)
    with pytest.raises(ValidationError):
        variant.full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        Variant.objects.filter(pk=variant.pk).update(**changes)


def test_variant_option_and_sku_uniqueness_are_database_enforced():
    variant = Variant.objects.first()
    with pytest.raises(IntegrityError), transaction.atomic():
        Variant.objects.create(
            product=variant.product,
            size=variant.size,
            color=variant.color,
            sku="DIFFERENT-SKU",
            price="10.00",
        )
    other = Variant.objects.exclude(pk=variant.pk).first()
    with pytest.raises(IntegrityError), transaction.atomic():
        Variant.objects.filter(pk=other.pk).update(sku=variant.sku)


def test_publishing_requires_date_in_validation_and_database():
    product = Product.objects.first()
    product.published_at = None
    with pytest.raises(ValidationError):
        product.full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        Product.objects.filter(pk=product.pk).update(published_at=None)


def test_departments_categories_collections_and_sale_are_real_queries(client):
    assert b"The Sculpted Wool Coat" in client.get("/shop/women/").content
    assert b"The Sculpted Wool Coat" not in client.get("/shop/men/").content
    assert b"The Fine Wool Knit" in client.get("/shop/men/").content
    assert b"The Everyday Tote" in client.get("/shop/accessories/").content
    assert b"The Everyday Tote" not in client.get("/shop/category/clothing/").content
    sale = client.get(reverse("catalog:sale"))
    assert b"The Pleated Trouser" in sale.content
    assert b"The Fine Wool Knit" not in sale.content
    signature = client.get("/collections/signature-edit/")
    assert b"The Pleated Trouser" not in signature.content
    Collection.objects.filter(slug="signature-edit").update(is_active=False)
    assert client.get("/collections/signature-edit/").status_code == 404
    assert b"The signature edit" not in client.get(reverse("catalog:collections")).content


@pytest.mark.parametrize("page", ["0", "-1", "abc", "1.1", "999999999999", "2", "١"])
def test_invalid_and_out_of_range_pages_return_404(client, page):
    assert client.get(reverse("catalog:all"), {"page": page}).status_code == 404


def test_pagination_is_bounded_and_stable(client):
    source = Product.objects.first()
    for index in range(11):
        product = Product.objects.create(
            name=f"Test piece {index}",
            slug=f"test-{index}",
            category=source.category,
            description="Test only",
            status="published",
            published_at=source.published_at,
        )
        variant = source.variants.first()
        Variant.objects.create(
            product=product,
            sku=f"TEST-{index}",
            size=variant.size,
            color=variant.color,
            price="12.50",
            stock=1,
        )
    response = client.get(reverse("catalog:all"))
    assert len(response.context["page_obj"]) == 12
    assert response.context["page_obj"].paginator.count == 15
    assert b'aria-label="Go to page 2"' in response.content
    assert b'aria-label="Page 1, current page"' in response.content
    assert len(client.get(reverse("catalog:all"), {"page": 2}).context["page_obj"]) == 3


@pytest.mark.parametrize(
    "params",
    [
        {"color": "missing", "size": "m", "quantity": "1"},
        {"color": "charcoal", "size": "missing", "quantity": "1"},
        {"color": "charcoal", "size": "m", "quantity": "0"},
        {"color": "charcoal", "size": "m", "quantity": "-1"},
        {"color": "charcoal", "size": "m", "quantity": "99"},
        {"color": "charcoal", "size": "m", "quantity": "1.5"},
        {"color": "charcoal", "size": "m", "quantity": "NaN"},
        {"quantity": "1"},
    ],
)
def test_bad_variant_selections_return_accessible_errors(client, params):
    response = client.get("/products/sculpted-coat/", params)
    assert response.status_code == 400
    assert b"Please check your selection" in response.content
    assert b'role="alert"' in response.content


def test_selection_uses_database_prices_and_availability(client):
    variant = Variant.objects.get(product__slug="sculpted-coat", size__slug="m")
    variant.price = Decimal("321.75")
    variant.save()
    response = client.get(
        "/products/sculpted-coat/",
        {
            "color": "charcoal",
            "size": "m",
            "quantity": "1",
            "price": "0.01",
        },
    )
    assert response.status_code == 200
    assert "€321.75" in response.content.decode()
    assert response.context["selected"].pk == variant.pk
    response = client.get(
        "/products/sculpted-coat/", {"color": "charcoal", "size": "l", "quantity": "1"}
    )
    assert b"This size is currently unavailable" in response.content
    variant.is_active = False
    variant.save()
    assert (
        client.get(
            "/products/sculpted-coat/", {"color": "charcoal", "size": "m", "quantity": "1"}
        ).status_code
        == 400
    )


def test_selection_must_match_color_and_size_on_the_same_variant(client):
    original = Variant.objects.get(product__slug="sculpted-coat", size__slug="xs")
    color = Color.objects.create(name="Slate", slug="slate")
    Variant.objects.create(
        product=original.product,
        sku="SLATE-XS",
        color=color,
        size=original.size,
        stock=2,
        price="335.50",
    )
    invalid = client.get(
        original.product.get_absolute_url(),
        {
            "color": "slate",
            "size": "m",
            "quantity": "1",
        },
    )
    assert invalid.status_code == 400
    assert b"This colour and size combination is unavailable" in invalid.content
    valid = client.get(
        original.product.get_absolute_url(),
        {
            "color": "slate",
            "size": "xs",
            "quantity": "1",
        },
    )
    assert valid.status_code == 200
    assert "€335.50" in valid.content.decode()
    assert b"Photography coming soon" in valid.content


def test_missing_photography_and_empty_catalog_have_honest_states(client):
    ProductImage.objects.all().delete()
    assert b"Photography coming soon" in client.get("/products/sculpted-coat/").content
    Product.objects.all().update(status="draft")
    response = client.get(reverse("catalog:all"))
    assert response.status_code == 200
    assert b"No pieces are published" in response.content
    assert b"New pieces will appear" in client.get(reverse("core:home")).content


def test_product_content_is_autoescaped(client):
    Product.objects.filter(slug="sculpted-coat").update(description="<script>alert(1)</script>")
    response = client.get("/products/sculpted-coat/")
    assert b"<script>alert" not in response.content
    assert b"&lt;script&gt;" in response.content


def test_listing_and_details_have_bounded_queries(client, django_assert_num_queries):
    with django_assert_num_queries(7):
        assert client.get(reverse("catalog:all")).status_code == 200
    with django_assert_num_queries(11):
        assert client.get("/products/sculpted-coat/").status_code == 200
    with django_assert_num_queries(8):
        assert client.get("/products/sculpted-coat/").status_code == 200
    with django_assert_num_queries(6):
        assert client.get(reverse("core:home")).status_code == 200


def test_seed_is_idempotent_and_preserves_admin_changes(settings, tmp_path):
    product = Product.objects.get(slug="sculpted-coat")
    product.name = "An edited name"
    product.save()
    product.variants.update(stock=19, price="333.33")
    initial_paths = set(ProductImage.objects.values_list("image", flat=True))
    # The original masters are valid inputs, but existing products are never rewritten.
    call_command("seed_catalog", verbosity=0)
    product.refresh_from_db()
    assert product.name == "An edited name"
    assert all(
        variant.stock == 19 and variant.price == Decimal("333.33")
        for variant in product.variants.all()
    )
    assert Product.objects.count() == 4
    assert Variant.objects.count() == 13
    assert set(ProductImage.objects.values_list("image", flat=True)) == initial_paths


def test_curated_styling_shows_only_public_companions(client):
    coat = Product.objects.get(slug="sculpted-coat")
    knit = Product.objects.get(slug="fine-wool-knit")
    tote = Product.objects.get(slug="everyday-tote")
    coat.styled_with.add(knit, tote, coat)
    Product.objects.filter(pk=knit.pk).update(status="draft")
    response = client.get(coat.get_absolute_url())
    assert response.status_code == 200
    assert list(response.context["related"]) == [tote]
    assert response.context["curated_styling"] is True
    assert b"Wear it with." in response.content


def test_selection_payload_uses_active_database_variants(client):
    product = Product.objects.get(slug="sculpted-coat")
    product.variants.filter(size__slug="m").update(price="321.75", stock=2)
    product.variants.filter(size__slug="xs").update(is_active=False)
    response = client.get(product.get_absolute_url())
    variants = response.context["selection_options"]["variants"]
    assert not any(item["size"] == "xs" for item in variants)
    medium = next(item for item in variants if item["size"] == "m")
    assert medium["price"] == "321.75"
    assert medium["maximum"] == 2
    assert next(item for item in variants if item["size"] == "l")["maximum"] == 0


def test_flagship_seed_preserves_images_curation_and_inventory(settings, tmp_path):
    sources = tmp_path / "assets/editorial/sources"
    for name in ("coat-styled", "coat-back", "coat-detail"):
        (sources / f"{name}.webp").write_bytes((sources / "coat.webp").read_bytes())
    settings.BASE_DIR = tmp_path
    coat = Product.objects.get(slug="sculpted-coat")
    original = coat.images.first()
    original.position = 2
    original.alt_text = "Owner's photograph"
    original.save()
    coat.styled_with.add(Product.objects.get(slug="everyday-tote"))
    coat.variants.update(stock=19, price="333.33")
    call_command("seed_editorial", verbosity=0)
    paths = set(coat.images.values_list("image", flat=True))
    call_command("seed_editorial", verbosity=0)
    original.refresh_from_db()
    assert original.alt_text == "Owner's photograph"
    assert original.position == 2
    assert set(coat.images.values_list("image", flat=True)) == paths
    assert coat.images.count() == 3
    assert list(coat.styled_with.values_list("slug", flat=True)) == ["everyday-tote"]
    assert coat.variants.filter(stock=19, price="333.33").count() == 4


def test_extended_seed_adds_image_matched_products_without_resetting_edits(settings, tmp_path):
    sources = tmp_path / "assets/editorial/sources"
    sample = (sources / "coat.webp").read_bytes()
    for piece in EXPANDED_PIECES:
        (sources / f"{piece.image}.webp").write_bytes(sample)
    settings.BASE_DIR = tmp_path
    Product.objects.filter(slug="sculpted-coat").update(name="Owner's coat")
    Variant.objects.filter(product__slug="sculpted-coat").update(stock=19, price="333.33")
    call_command("seed_catalog", extended=True, verbosity=0)
    assert Product.objects.count() == 14
    assert Variant.objects.count() == 50
    assert ProductImage.objects.count() == 14
    assert Product.objects.filter(department="men").count() == 5
    assert Product.objects.filter(department="accessories").count() == 2
    assert Product.objects.get(slug="sculpted-coat").name == "Owner's coat"
    assert (
        Variant.objects.filter(product__slug="sculpted-coat", stock=19, price="333.33").count() == 4
    )
    Variant.objects.filter(product__slug="wool-overshirt").update(stock=23)
    paths = set(ProductImage.objects.values_list("image", flat=True))
    call_command("seed_catalog", extended=True, verbosity=0)
    assert Product.objects.count() == 14
    assert set(ProductImage.objects.values_list("image", flat=True)) == paths
    assert Variant.objects.filter(product__slug="wool-overshirt", stock=23).count() == 4


def test_extended_seed_checks_all_masters_before_writing(settings, tmp_path):
    settings.BASE_DIR = tmp_path
    with pytest.raises(CommandError, match="masters are missing"):
        call_command("seed_catalog", extended=True, verbosity=0)
    assert Product.objects.count() == 4
    assert Variant.objects.count() == 13


@pytest.mark.parametrize("route", ["/shop/", "/collections/"])
def test_catalog_is_read_only_with_noindex_and_security_headers(client, route):
    assert client.post(route).status_code == 405
    response = client.get(route)
    assert "noindex" in response["X-Robots-Tag"]
    assert "script-src 'self'" in response["Content-Security-Policy"]
