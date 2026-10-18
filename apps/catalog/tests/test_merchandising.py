import pytest
from django.core.management import call_command

from apps.catalog.management.commands.seed_merchandising import SIGNATURES, VIEWS
from apps.catalog.models import Collection, Color, Product, ProductImage
from apps.core.editorial import EXPANDED_PIECES

pytestmark = [pytest.mark.django_db, pytest.mark.usefixtures("catalog_data")]


@pytest.mark.parametrize("hidden", ["draft", "inactive_variants"])
def test_collection_and_campaign_covers_do_not_expose_hidden_products(client, hidden):
    product = Product.objects.get(slug="sculpted-coat")
    collection = Collection.objects.get(slug="autumn-winter-26")
    collection.cover_image = product.images.first()
    collection.save()
    assert client.get("/").context["campaign"].pk == collection.pk
    assert client.get(collection.get_absolute_url()).context["collection"].cover_is_public
    if hidden == "draft":
        Product.objects.filter(pk=product.pk).update(status="draft")
    else:
        product.variants.update(is_active=False)
    assert client.get("/").context["campaign"] is None
    assert not client.get(collection.get_absolute_url()).context["collection"].cover_is_public


def test_card_alternate_photograph_matches_primary_colour(client):
    product = Product.objects.get(slug="sculpted-coat")
    first = product.images.first()
    other = Color.objects.create(slug="slate", name="Slate")
    ProductImage.objects.create(
        product=product, color=other, image=first.image.name, alt_text="Other colour", position=1
    )
    matching = ProductImage.objects.create(
        product=product,
        color=first.color,
        image=first.image.name,
        alt_text="Matching alternate",
        position=2,
    )
    piece = Product.objects.for_display().get(pk=product.pk)
    assert piece.alternate_image.pk == matching.pk
    assert b"Original price" in client.get("/shop/sale/").content


def test_merchandising_seed_preserves_owner_content_and_inventory(settings, tmp_path):
    sources = tmp_path / "assets/editorial/sources"
    sample = (sources / "coat.webp").read_bytes()
    for piece in EXPANDED_PIECES:
        (sources / f"{piece.image}.webp").write_bytes(sample)
    for asset in SIGNATURES.values():
        for view, _ in VIEWS:
            (sources / f"{asset}-{view}.webp").write_bytes(sample)
    settings.BASE_DIR = tmp_path
    call_command("seed_catalog", extended=True, verbosity=0)
    knit = Product.objects.get(slug="fine-wool-knit")
    knit.variants.update(price="333.33", stock=19)
    owner_cover = knit.images.first()
    Collection.objects.filter(slug="signature-edit").update(cover_image=owner_cover)
    call_command("seed_merchandising", verbosity=0)
    paths = set(ProductImage.objects.values_list("image", flat=True))
    call_command("seed_merchandising", verbosity=0)
    assert set(ProductImage.objects.values_list("image", flat=True)) == paths
    assert all(Product.objects.get(slug=slug).images.count() == 4 for slug in SIGNATURES)
    assert Collection.objects.get(slug="signature-edit").cover_image_id == owner_cover.pk
    assert knit.variants.filter(price="333.33", stock=19).count() == 4
