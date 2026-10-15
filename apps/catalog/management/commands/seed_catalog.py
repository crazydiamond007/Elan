"""Create a small, image-matched fictional capsule; leave existing records untouched."""

from decimal import Decimal

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Category, Collection, Color, Product, ProductImage, Size, Variant
from apps.core.editorial import EXPANDED_PIECES, PIECES


class Command(BaseCommand):
    help = "Create missing fictional catalog records without resetting existing data or stock."

    def add_arguments(self, parser):
        parser.add_argument(
            "--extended",
            action="store_true",
            help="Include the ten additional image-matched fictional pieces.",
        )

    def handle(self, *args, **options):
        source = settings.BASE_DIR / "assets/editorial/sources"
        pieces = PIECES + EXPANDED_PIECES if options["extended"] else PIECES
        if any(not (source / f"{piece.image}.webp").is_file() for piece in pieces):
            raise CommandError("The approved product image masters are missing.")
        with transaction.atomic():
            clothing, _ = Category.objects.get_or_create(
                slug="clothing", defaults={"name": "Clothing"}
            )
            accessories, _ = Category.objects.get_or_create(
                slug="accessories", defaults={"name": "Accessories"}
            )
            autumn, _ = Collection.objects.get_or_create(
                slug="autumn-winter-26",
                defaults={
                    "name": "A softer season",
                    "description": "Autumn / Winter 26. Soft structure, warm neutrals "
                    "and a quieter rhythm.",
                    "is_featured": True,
                },
            )
            signature, _ = Collection.objects.get_or_create(
                slug="signature-edit",
                defaults={
                    "name": "The signature edit",
                    "description": "A curated demonstration edit of the pieces we return to.",
                    "is_featured": True,
                },
            )
            sizes = {}
            for position, label in enumerate(("XS", "S", "M", "L", "One size")):
                slug = label.lower().replace(" ", "-")
                sizes[label], _ = Size.objects.get_or_create(
                    slug=slug, defaults={"name": label, "position": position}
                )
            created = 0
            for index, piece in enumerate(pieces):
                is_accessory = piece.departments == ("accessories",)
                color, _ = Color.objects.get_or_create(
                    slug=piece.color.lower(), defaults={"name": piece.color}
                )
                department = (
                    "accessories"
                    if is_accessory
                    else "unisex"
                    if len(piece.departments) > 1
                    else piece.departments[0]
                )
                composition = {
                    "coat": "Imagined wool-rich fabric with a smooth lining.",
                    "knit": "Imagined fine-gauge wool knit.",
                    "trousers": "Imagined wool-blend woven fabric.",
                    "bag": "Imagined leather outer and textile lining.",
                }.get(piece.image, piece.composition)
                product, new = Product.objects.get_or_create(
                    slug=piece.slug,
                    defaults={
                        "name": piece.name,
                        "description": piece.description,
                        "department": department,
                        "category": accessories if is_accessory else clothing,
                        "composition": composition,
                        "care": "Fictional product: follow the care label of any real garment. "
                        "For this imagined piece, use specialist cleaning and store away "
                        "from direct heat.",
                        "fit": "One size. Illustrative proportions."
                        if is_accessory
                        else "Relaxed proportions. Sizes are illustrative; no physical garment "
                        "measurements are available.",
                        "status": "published",
                        "published_at": timezone.now(),
                        "is_featured": True,
                        "is_signature": piece.image
                        in {
                            "coat",
                            "knit",
                            "bag",
                            "overshirt",
                            "tailored-blazer",
                            "merino-cardigan",
                        },
                    },
                )
                if not new:
                    continue
                product.collections.add(autumn)
                if product.is_signature:
                    product.collections.add(signature)
                for position, label in enumerate(
                    ("One size",) if is_accessory else ("XS", "S", "M", "L")
                ):
                    variant = Variant(
                        product=product,
                        sku=f"ME-{index + 1:03}-{sizes[label].slug.upper()}",
                        color=color,
                        size=sizes[label],
                        price=Decimal("160.00") if piece.image == "trousers" else piece.price,
                        compare_at_price=piece.price if piece.image == "trousers" else None,
                        stock=0 if label == "L" else 4 + position,
                    )
                    variant.full_clean()
                    variant.save()
                with (source / f"{piece.image}.webp").open("rb") as master:
                    image = ProductImage(
                        product=product,
                        color=color,
                        alt_text=f"{piece.name} in {piece.color.lower()}, "
                        "photographed against warm ivory.",
                    )
                    image.image = File(master, name=f"{piece.image}.webp")
                    image.full_clean(exclude=["small", "medium"])
                    image.save()
                created += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created} fictional products. Existing products and stock were preserved."
            )
        )
