import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.catalog.models import Product, ProductImage, Variant

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


@pytest.mark.django_db
def test_images_whose_files_vanished_are_discarded_so_seeding_can_replace_them(catalog_data):
    from apps.catalog.models import ProductImage

    image = ProductImage.objects.first()
    assert image is not None
    product_id = image.product_id
    surviving = ProductImage.objects.exclude(pk=image.pk).count()
    # Simulate media seeded onto a container filesystem that was then replaced.
    image.image.storage.delete(image.image.name)

    call_command("bootstrap_deployment", skip_seed=False, verbosity=0)

    assert not ProductImage.objects.filter(pk=image.pk).exists()
    # Rows whose files are intact are untouched, and seeding refills the gap.
    assert ProductImage.objects.count() >= surviving
    front = ProductImage.objects.get(product_id=product_id, position=0)
    assert all(
        field.storage.exists(field.name) for field in (front.image, front.small, front.medium)
    )


@pytest.mark.django_db
def test_images_with_intact_files_are_kept(catalog_data):
    from apps.catalog.models import ProductImage

    before = set(ProductImage.objects.values_list("pk", flat=True))
    assert before
    call_command("bootstrap_deployment", skip_seed=False, verbosity=0)
    assert before <= set(ProductImage.objects.values_list("pk", flat=True))


@pytest.fixture
def deployed_catalog(catalog_data, settings, tmp_path, monkeypatch):
    """Exercise every startup seed with small, valid masters and isolated media."""
    sources = tmp_path / "assets/editorial/sources"
    sample = (sources / "coat.webp").read_bytes()
    for master in (settings.BASE_DIR / "assets/editorial/sources").glob("*.webp"):
        (sources / master.name).write_bytes(sample)
    settings.BASE_DIR = tmp_path
    monkeypatch.delenv("DJANGO_SUPERUSER_USERNAME", raising=False)
    monkeypatch.delenv("DJANGO_SUPERUSER_PASSWORD", raising=False)
    call_command("bootstrap_deployment", verbosity=0)


def catalog_snapshot():
    return {
        "products": list(Product.objects.order_by("pk").values()),
        "variants": list(Variant.objects.order_by("pk").values()),
        "collections": set(Product.collections.through.objects.values_list()),
        "styling": set(Product.styled_with.through.objects.values_list()),
    }


@pytest.mark.django_db
def test_bootstrap_restores_all_lost_media_without_resetting_catalog_edits(deployed_catalog):
    product = Product.objects.get(slug="merino-cardigan")
    product.name = "Owner-edited cardigan"
    product.save()
    product.variants.update(price="333.33", stock=19)
    before = catalog_snapshot()
    assert ProductImage.objects.count() == 32
    for photo in ProductImage.objects.all():
        for field in (photo.image, photo.small, photo.medium):
            field.storage.delete(field.name)

    call_command("bootstrap_deployment", verbosity=0)

    assert catalog_snapshot() == before
    assert ProductImage.objects.count() == 32
    assert set(ProductImage.objects.filter(position=0).values_list("product_id", flat=True)) == set(
        Product.objects.values_list("pk", flat=True)
    )
    for photo in ProductImage.objects.all():
        for field in (photo.image, photo.small, photo.medium):
            assert field.storage.exists(field.name)
    recovered = set(ProductImage.objects.values_list("pk", "image", "small", "medium"))
    call_command("bootstrap_deployment", verbosity=0)
    assert set(ProductImage.objects.values_list("pk", "image", "small", "medium")) == recovered
    assert catalog_snapshot() == before


@pytest.mark.django_db
def test_bootstrap_recovers_the_partial_state_left_by_the_failed_startup(deployed_catalog):
    ProductImage.objects.all().delete()
    call_command("seed_editorial", verbosity=0)
    surviving = set(ProductImage.objects.values_list("pk", flat=True))
    assert len(surviving) == 3

    call_command("bootstrap_deployment", verbosity=0)

    assert ProductImage.objects.count() == 32
    assert surviving <= set(ProductImage.objects.values_list("pk", flat=True))
    assert Product.objects.get(slug="sculpted-coat").images.filter(position=0).exists()


@pytest.mark.django_db
def test_regular_catalog_seed_still_leaves_existing_products_untouched(deployed_catalog):
    product = Product.objects.get(slug="merino-cardigan")
    product.images.filter(position=0).delete()

    call_command("seed_catalog", extended=True, verbosity=0)

    assert not product.images.filter(position=0).exists()


@pytest.mark.django_db
def test_bootstrap_keeps_custom_front_images_and_the_merchandising_guard(deployed_catalog):
    product = Product.objects.get(slug="merino-cardigan")
    front = product.images.get(position=0)
    front.color = Product.objects.get(slug="fine-wool-knit").images.get(position=0).color
    front.save(update_fields=["color"])
    images_before = list(ProductImage.objects.order_by("pk").values())

    with pytest.raises(CommandError, match="front photograph for merino-cardigan"):
        call_command("bootstrap_deployment", verbosity=0)

    assert list(ProductImage.objects.order_by("pk").values()) == images_before


@pytest.mark.django_db
def test_recovery_does_not_recreate_an_owner_removed_colour(deployed_catalog):
    product = Product.objects.get(slug="merino-cardigan")
    product.images.filter(position=0).delete()
    other_color = Product.objects.get(slug="fine-wool-knit").images.get(position=0).color
    product.variants.update(color=other_color)
    before = catalog_snapshot()

    call_command("seed_catalog", extended=True, restore_missing_images=True, verbosity=0)

    assert not product.images.filter(position=0).exists()
    assert catalog_snapshot() == before
