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
