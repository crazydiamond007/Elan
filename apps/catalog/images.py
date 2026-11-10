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

# The storefront sits on a single flat ivory. Studio masters arrive with slightly different
# backdrops, so a grid of untouched derivatives reads as a patchwork of near-ivory rectangles.
BACKDROP = "#F7F5F0"
BACKDROP_RGB = (247, 245, 240)
# Guards keep the correction to genuine pale studio backdrops. Editorial scenes fail the
# brightness test, uneven borders fail the deviation test, and no channel is ever moved far
# enough to restyle a photograph.
BACKDROP_MIN_LEVEL = 200
BACKDROP_MAX_DEVIATION = 12
BACKDROP_MAX_SHIFT = 32


def _edge_statistics(image):
    """Per-channel median and median absolute deviation around the image border.

    Both statistics are robust, so a subject that reaches the frame edge shifts them far less
    than it would shift a mean and standard deviation.
    """
    sample = image.resize((96, 96), Image.Resampling.BILINEAR)
    width, height = sample.size
    inset = 6
    border = [
        sample.getpixel((x, y))
        for y in range(height)
        for x in range(width)
        if y < inset or y >= height - inset or x < inset or x >= width - inset
    ]
    medians, deviations = [], []
    for channel in range(3):
        values = sorted(pixel[channel] for pixel in border)
        median = values[len(values) // 2]
        spread = sorted(abs(value - median) for value in values)
        medians.append(median)
        deviations.append(spread[len(spread) // 2])
    return medians, deviations


def normalize_backdrop(image):
    """Move a uniform pale studio backdrop onto the storefront ivory.

    Each channel is remapped through (0, 0), (measured, target) and (255, 255), so the backdrop
    lands exactly on the page colour while the black and white points stay fixed. Photographs
    whose borders are dark, uneven or far from ivory are returned unchanged.
    """
    medians, deviations = _edge_statistics(image)
    pairs = list(zip(medians, BACKDROP_RGB, strict=True))
    if min(medians) < BACKDROP_MIN_LEVEL:
        return image
    if max(deviations) > BACKDROP_MAX_DEVIATION:
        return image
    if any(abs(target - measured) > BACKDROP_MAX_SHIFT for measured, target in pairs):
        return image
    if all(measured == target for measured, target in pairs):
        return image
    lookup = []
    for measured, target in pairs:
        for level in range(256):
            if level <= measured:
                mapped = target * level / measured if measured else level
            else:
                mapped = target + (255 - target) * (level - measured) / (255 - measured)
            lookup.append(min(255, max(0, round(mapped))))
    return image.point(lookup)


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
            clean = Image.new("RGB", oriented.size, BACKDROP)
            clean.paste(oriented, mask=oriented.getchannel("A"))
            clean = normalize_backdrop(clean)
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
