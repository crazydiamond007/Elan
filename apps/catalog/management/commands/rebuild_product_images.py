"""Re-run the image pipeline over stored product media.

Derivatives are generated once, at upload. When the pipeline itself changes -- as it did when
backdrop normalisation was added -- existing media keeps the older treatment until it is
re-derived. Masters are never touched; this command re-derives from the stored files.
"""

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import ProductImage


class Command(BaseCommand):
    help = "Regenerate stored product image derivatives through the current pipeline."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be rebuilt without writing any files.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        rebuilt = failed = 0
        for image in ProductImage.objects.select_related("product").order_by("pk"):
            label = f"{image.product.slug} #{image.pk}"
            if not image.image:
                self.stdout.write(f"  skipped {label}: no stored file")
                continue
            if dry_run:
                self.stdout.write(f"  would rebuild {label}")
                rebuilt += 1
                continue
            try:
                with image.image.open("rb") as stored:
                    payload = stored.read()
                superseded = [
                    (field.storage, field.name)
                    for field in (image.image, image.small, image.medium)
                    if field
                ]
                with transaction.atomic():
                    image.image = ContentFile(payload, name="rebuild.webp")
                    image.save()
            except Exception as error:  # noqa: BLE001 - report and continue over the catalog
                failed += 1
                self.stderr.write(f"  failed {label}: {error}")
                continue
            current = {field.name for field in (image.image, image.small, image.medium)}
            for storage, name in superseded:
                if name not in current:
                    storage.delete(name)
            rebuilt += 1
            self.stdout.write(f"  rebuilt {label}")
        verb = "would rebuild" if dry_run else "rebuilt"
        self.stdout.write(self.style.SUCCESS(f"{verb} {rebuilt} image(s); {failed} failed"))
