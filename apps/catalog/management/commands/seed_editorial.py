"""Add the flagship gallery and curated outfit without replacing existing content."""

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Product, ProductImage

GALLERY = (
    ("coat-styled", "The charcoal Sculpted Wool Coat worn over ivory knit and black trousers."),
    ("coat-back", "Back view of the charcoal Sculpted Wool Coat, showing its seam and hem vent."),
    ("coat-detail", "Close detail of the coat’s charcoal wool, notched lapel and dark button."),
)


class Command(BaseCommand):
    help = "Add missing flagship photographs and styling links; preserve existing catalog edits."

    def handle(self, *args, **options):
        source = settings.BASE_DIR / "assets/editorial/sources"
        if any(not (source / f"{name}.webp").is_file() for name, _ in GALLERY):
            raise CommandError("The flagship image masters are missing.")
        product = Product.objects.filter(slug="sculpted-coat").first()
        if product is None:
            raise CommandError("Run seed_catalog before seed_editorial.")
        color = (
            product.variants.filter(color__slug="charcoal")
            .values_list("color_id", flat=True)
            .first()
        )
        if color is None:
            raise CommandError(
                "The flagship coat has no charcoal variant; existing edits preserved."
            )
        created = 0
        with transaction.atomic():
            for position, (name, description) in enumerate(GALLERY, start=1):
                # Occupied positions belong to the owner; never replace or reorder them.
                if product.images.filter(position=position).exists():
                    continue
                with (source / f"{name}.webp").open("rb") as master:
                    image = ProductImage(
                        product=product, color_id=color, position=position, alt_text=description
                    )
                    image.image = File(master, name=f"{name}.webp")
                    image.full_clean(exclude=["small", "medium"])
                    image.save()
                created += 1
            if not product.styled_with.exists():
                product.styled_with.add(
                    *Product.objects.filter(
                        slug__in=["fine-wool-knit", "pleated-trouser", "everyday-tote"]
                    )
                )
        self.stdout.write(
            self.style.SUCCESS(f"Added {created} flagship photographs; existing edits preserved.")
        )
