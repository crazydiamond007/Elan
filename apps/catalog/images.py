"""Bounded decoding and metadata-free WebP derivatives for trusted staff uploads.

Storage uses generated names; original filenames and original upload bytes are never served.
Serving media from a separate, cookie-free origin remains a deployment requirement.
"""

import warnings
from io import BytesIO
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 20_000_000


def validate_image(upload):
    if upload.size > MAX_BYTES:
        raise ValidationError("Choose an image smaller than 8 MiB.")
    try:
        upload.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError("Use a JPEG, PNG or WebP image.")
                if image.width * image.height > MAX_PIXELS:
                    raise ValidationError("Images must contain no more than 20 million pixels.")
                if image.width < 100 or image.height < 100:
                    raise ValidationError("Images must be at least 100 pixels on each side.")
                if getattr(image, "n_frames", 1) != 1:
                    raise ValidationError("Animated images are not supported.")
                image.verify()
            upload.seek(0)
            with Image.open(upload) as decoded:
                decoded.load()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombWarning,
        Image.DecompressionBombError,
    ) as error:
        raise ValidationError("The image could not be read safely.") from error
    finally:
        upload.seek(0)


def derivatives(upload):
    validate_image(upload)
    try:
        with Image.open(upload) as source:
            source.load()
            oriented = ImageOps.exif_transpose(source).convert("RGBA")
            clean = Image.new("RGB", oriented.size, "#F7F5F0")
            clean.paste(oriented, mask=oriented.getchannel("A"))
    except (OSError, ValueError) as error:
        raise ValidationError("The image could not be decoded safely.") from error
    identifier = uuid4().hex
    results = {}
    for field, width in (("image", 1600), ("small", 480), ("medium", 960)):
        resized = clean.copy()
        resized.thumbnail((width, width * 4), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        resized.save(buffer, format="WEBP", quality=84, method=6)
        results[field] = (
            ContentFile(buffer.getvalue(), name=f"{identifier}-{width}.webp"),
            resized.width,
            resized.height,
        )
    return results


def product_image_path(instance, filename):
    # Both the directory and filenames are generated independently of user input.
    return f"products/{instance.product_id}/{uuid4().hex}.webp"
