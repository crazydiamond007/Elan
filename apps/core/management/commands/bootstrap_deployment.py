"""Bring a hosted deployment to a serving state: schema, demonstration catalog, administrator.

Written for platforms that offer no separate migration step, so it runs on every container start
and must be safe to repeat. Each stage is idempotent: migrations are already no-ops once applied,
the seed commands skip records that exist, and the administrator is only created when absent.

docs/deployment.md keeps migrations manual for the reviewed Compose deployment. This command runs
only when DJANGO_BOOTSTRAP_ON_START is set, so that boundary is unchanged unless a deployment opts
in deliberately.
"""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import ProductImage


class Command(BaseCommand):
    help = "Apply migrations, seed the demonstration catalog and ensure an administrator exists."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-seed",
            action="store_true",
            help="Apply migrations and the administrator without seeding catalog records.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Applying migrations")
        call_command("migrate", "--noinput", verbosity=0)

        if options["skip_seed"]:
            self.stdout.write("Skipping catalog seed")
        else:
            self._discard_images_whose_files_are_gone()
            self.stdout.write("Seeding the demonstration catalog")
            call_command("seed_catalog", "--extended", verbosity=0)
            call_command("seed_editorial", verbosity=0)
            call_command("seed_merchandising", verbosity=0)

        self._ensure_administrator()
        self.stdout.write(self.style.SUCCESS("Deployment is ready to serve"))

    def _discard_images_whose_files_are_gone(self):
        """Delete catalog image rows whose stored files no longer exist.

        The database outlives the container, but media on a container filesystem does not. A
        deployment that seeded before a persistent volume was attached is left with rows that
        reference files nothing can serve, and the seed commands skip those products because a
        row is already present. Dropping the unusable rows lets the seeds recreate them, which
        makes the deployment repair itself once storage actually persists.
        """
        stranded = []
        for image in ProductImage.objects.all():
            files = (image.image, image.small, image.medium)
            if any(not field.name or not field.storage.exists(field.name) for field in files):
                stranded.append(image.pk)
        if not stranded:
            return
        ProductImage.objects.filter(pk__in=stranded).delete()
        self.stdout.write(
            self.style.WARNING(
                f"Discarded {len(stranded)} image(s) whose files were missing so they can be "
                "recreated. Attach persistent storage at MEDIA_ROOT to stop this recurring."
            )
        )

    def _ensure_administrator(self):
        """Create the administrator named by the environment, once.

        An existing account is never modified: silently resetting a password on every restart
        would undo a deliberate change made through the admin, and would make the environment
        variable a standing instruction to overwrite rather than a one-time starting point.
        """
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        if not username or not password:
            self.stdout.write(
                "No administrator created: set DJANGO_SUPERUSER_USERNAME and "
                "DJANGO_SUPERUSER_PASSWORD to create one."
            )
            return

        users = get_user_model()
        if users.objects.filter(username=username).exists():
            self.stdout.write(f"Administrator {username!r} already exists; leaving it unchanged")
            return

        # The project keeps Django's validators enabled, so a weak password fails loudly here
        # rather than producing an account that cannot be defended.
        try:
            validate_password(password)
        except ValidationError as error:
            raise CommandError(
                "DJANGO_SUPERUSER_PASSWORD was rejected: " + " ".join(error.messages)
            ) from error

        with transaction.atomic():
            users.objects.create_superuser(username=username, email=email or "", password=password)
        self.stdout.write(self.style.SUCCESS(f"Created administrator {username!r}"))
