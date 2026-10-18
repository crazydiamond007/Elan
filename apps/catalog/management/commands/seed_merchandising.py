"""Add signature galleries and collection covers, preserving existing content and stock."""

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Collection, Product, ProductImage

SIGNATURES = {
    "fine-wool-knit": "knit",
    "everyday-tote": "bag",
    "wool-overshirt": "overshirt",
    "tailored-blazer": "tailored-blazer",
    "merino-cardigan": "merino-cardigan",
}
VIEWS = (("styled", "Styled view"), ("back", "Back view"), ("detail", "Material detail"))
COLORS = {
    "fine-wool-knit": "ivory",
    "everyday-tote": "black",
    "wool-overshirt": "chocolate",
    "tailored-blazer": "taupe",
    "merino-cardigan": "oatmeal",
}
OUTFITS = {
    "fine-wool-knit": ("tailored-blazer", "pleated-trouser", "everyday-tote"),
    "everyday-tote": ("sculpted-coat", "fine-wool-knit", "pleated-trouser"),
    "wool-overshirt": ("linen-shirt", "pleated-trouser", "brushed-wool-scarf"),
    "tailored-blazer": ("fine-wool-knit", "pleated-midi-skirt", "everyday-tote"),
    "merino-cardigan": ("linen-shirt", "pleated-trouser", "brushed-wool-scarf"),
}


class Command(BaseCommand):
    help = "Add missing signature photographs, collection covers and curated outfit links."

    def handle(self, *args, **options):
        source = settings.BASE_DIR / "assets/editorial/sources"
        if any(
            not (source / f"{asset}-{view}.webp").is_file()
            for asset in SIGNATURES.values()
            for view, _ in VIEWS
        ):
            raise CommandError("The signature gallery masters are missing.")
        products = {item.slug: item for item in Product.objects.filter(slug__in=SIGNATURES)}
        if products.keys() != SIGNATURES.keys():
            raise CommandError("Run seed_catalog --extended before seed_merchandising.")
        colors = {}
        for slug, product in products.items():
            # Anchor the photos to the existing front view, rather than guessing a colour.
            front = product.images.select_related("color").order_by("position", "pk").first()
            if front is None or front.color_id is None or front.color.slug != COLORS[slug]:
                raise CommandError(
                    f"The front photograph for {slug} differs from the seed; edits preserved."
                )
            colors[slug] = front.color_id
        created = 0
        with transaction.atomic():
            for slug, asset in SIGNATURES.items():
                product = products[slug]
                for position, (view, label) in enumerate(VIEWS, start=1):
                    if product.images.filter(position=position).exists():
                        continue
                    with (source / f"{asset}-{view}.webp").open("rb") as master:
                        image = ProductImage(
                            product=product,
                            color_id=colors[slug],
                            position=position,
                            alt_text=f"{label} of {product.name}.",
                        )
                        image.image = File(master, name=f"{asset}-{view}.webp")
                        image.full_clean(exclude=["small", "medium"])
                        image.save()
                    created += 1
                if not product.styled_with.exists():
                    product.styled_with.add(*Product.objects.filter(slug__in=OUTFITS[slug]))
            for slug, product_slug in (
                ("autumn-winter-26", "fine-wool-knit"),
                ("signature-edit", "tailored-blazer"),
            ):
                cover = products[product_slug].images.filter(position=1).first()
                Collection.objects.filter(slug=slug, cover_image__isnull=True).update(
                    cover_image=cover
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"Added {created} signature photographs; "
                "existing images, covers, curation and stock preserved."
            )
        )
