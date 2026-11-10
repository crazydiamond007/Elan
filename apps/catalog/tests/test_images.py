from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.catalog import images
from apps.catalog.forms import ProductImageForm
from apps.catalog.models import Product, ProductImage


def upload(name="photo.jpg", size=(150, 200), format="JPEG", **kwargs):
    buffer = BytesIO()
    Image.new("RGB", size, "white").save(buffer, format, **kwargs)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


@pytest.mark.parametrize(
    "content", [b"<svg><script>alert(1)</script></svg>", b"<html>hi</html>", b"", b"RIFFbrokenWEBP"]
)
def test_unsupported_or_corrupt_uploads_are_rejected(content):
    with pytest.raises(ValidationError):
        images.derivatives(SimpleUploadedFile("fake.jpg", content, content_type="image/jpeg"))


def test_byte_and_pixel_limits_are_enforced(monkeypatch):
    monkeypatch.setattr(images, "MAX_BYTES", 10)
    with pytest.raises(ValidationError, match="8 MiB"):
        images.validate_image(upload())
    monkeypatch.setattr(images, "MAX_BYTES", 8 * 1024 * 1024)
    monkeypatch.setattr(images, "MAX_PIXELS", 1000)
    with pytest.raises(ValidationError, match="20 million"):
        images.validate_image(upload())


def test_tiny_and_animated_images_are_rejected():
    with pytest.raises(ValidationError, match="100 pixels"):
        images.validate_image(upload(size=(50, 50)))
    buffer = BytesIO()
    Image.new("RGB", (150, 200), "white").save(
        buffer,
        "WEBP",
        save_all=True,
        append_images=[Image.new("RGB", (150, 200), "black")],
        duration=100,
        loop=0,
    )
    with pytest.raises(ValidationError, match="Animated"):
        images.validate_image(SimpleUploadedFile("animated.webp", buffer.getvalue()))


def test_truncated_image_is_rejected_during_full_decode():
    source = upload()
    with pytest.raises(ValidationError):
        images.derivatives(SimpleUploadedFile("broken.jpg", source.read()[:-100]))


@pytest.mark.django_db
def test_images_are_reencoded_without_metadata_or_user_filenames(catalog_data):
    exif = Image.Exif()
    exif[315] = "private metadata"
    image = ProductImage(product=Product.objects.first(), alt_text="Test garment")
    image.image = upload("../../private.php.jpg", size=(1200, 1600), exif=exif)
    image.save()
    for field in (image.image, image.small, image.medium):
        assert field.name.startswith(f"products/{image.product_id}/")
        assert field.name.endswith(".webp")
        assert "private" not in field.name and ".." not in field.name
        with field.open("rb") as source, Image.open(source) as processed:
            assert processed.format == "WEBP"
            assert not processed.getexif()
            assert "icc_profile" not in processed.info
            assert "xmp" not in processed.info
    assert image.width == 1200 and image.height == 1600
    assert image.small_width == 480 and image.medium_width == 960


@pytest.mark.django_db
def test_programmatic_saves_cannot_bypass_image_validation(catalog_data):
    image = ProductImage(product=Product.objects.first(), alt_text="Invalid image")
    image.image = SimpleUploadedFile("looks-valid.jpg", b"not an image")
    with pytest.raises(ValidationError):
        image.save()
    assert not image.pk


@pytest.mark.django_db
def test_admin_upload_form_reports_decode_errors_without_saving(catalog_data):
    source = upload()
    form = ProductImageForm(
        data={"product": Product.objects.first().pk, "alt_text": "Test image", "position": 0},
        files={"image": SimpleUploadedFile("truncated.jpg", source.read()[:-100])},
    )
    assert not form.is_valid()
    assert "image" in form.errors
    assert form.instance.pk is None


@pytest.mark.django_db
def test_alt_text_is_required_by_model_validation(catalog_data):
    image = ProductImage(product=Product.objects.first(), image=upload(), alt_text="")
    with pytest.raises(ValidationError) as failure:
        image.full_clean(exclude=["small", "medium"])
    assert "alt_text" in failure.value.message_dict


def packshot(backdrop, subject="#303030", size=(300, 400)):
    """A pale studio frame with a centred subject, as product masters are composed."""
    image = Image.new("RGB", size, backdrop)
    inset_x, inset_y = size[0] // 4, size[1] // 4
    image.paste(
        Image.new("RGB", (size[0] // 2, size[1] // 2), subject),
        (inset_x, inset_y),
    )
    return image


def test_uniform_pale_backdrops_are_moved_onto_the_storefront_ivory():
    for backdrop in ("#E8E5DE", "#FBF8F2", "#F0EBE3"):
        normalized = images.normalize_backdrop(packshot(backdrop))
        medians, _ = images._edge_statistics(normalized)
        assert all(
            abs(measured - target) <= 1
            for measured, target in zip(medians, images.BACKDROP_RGB, strict=True)
        ), f"{backdrop} did not land on the ivory backdrop: {medians}"


def test_normalisation_preserves_the_black_point_of_the_subject():
    original = packshot("#E8E5DE", subject="#000000")
    normalized = images.normalize_backdrop(original)
    assert normalized is not original
    assert normalized.getpixel((150, 200)) == (0, 0, 0)


def test_editorial_scenes_are_left_untouched():
    # A dark, uneven border is a scene rather than a packshot.
    scene = Image.new("RGB", (300, 400), "#8A7A68")
    assert images.normalize_backdrop(scene) is scene
    # A bright but strongly patterned border is a scene too: broad bands survive the
    # downscale and push the median absolute deviation past the guard.
    banded = packshot("#FFFFFF")
    for y in range(0, 400, 48):
        banded.paste(Image.new("RGB", (300, 24), "#D2D2D2"), (0, y))
    assert images.normalize_backdrop(banded) is banded


def test_backdrops_already_on_ivory_are_returned_unchanged():
    exact = packshot("#F7F5F0")
    assert images.normalize_backdrop(exact) is exact


@pytest.mark.django_db
def test_derivatives_normalise_the_backdrop_of_uploaded_packshots(catalog_data):
    buffer = BytesIO()
    packshot("#E8E5DE").resize((1200, 1600)).save(buffer, "WEBP", quality=94)
    image = ProductImage(product=Product.objects.first(), alt_text="Packshot")
    image.image = SimpleUploadedFile("packshot.webp", buffer.getvalue())
    image.save()
    with image.image.open("rb") as source, Image.open(source) as processed:
        processed.load()
        medians, _ = images._edge_statistics(processed.convert("RGB"))
    assert all(
        abs(measured - target) <= 2
        for measured, target in zip(medians, images.BACKDROP_RGB, strict=True)
    ), medians
