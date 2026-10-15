import os
import subprocess
from pathlib import Path

import pytest

from apps.catalog.models import Product


@pytest.mark.skipif(
    os.environ.get("MAISON_BROWSER_QA") != "1", reason="Optional browser tooling outside project"
)
@pytest.mark.django_db(transaction=True)
def test_rendered_admin_journey(live_server, django_user_model, catalog_data, settings):
    username, password = "isolated-browser-editor", "Test-only-browser-password-2026"
    django_user_model.objects.create_superuser(username=username, password=password)
    product = Product.objects.get(slug="sculpted-coat")
    environment = {name: os.environ[name] for name in ("PATH", "HOME") if name in os.environ}
    environment.update(
        PLAYWRIGHT_BROWSERS_PATH="/tmp/maison-elan-browser/browsers",
        MAISON_BASE_URL=live_server.url,
        MAISON_ADMIN_USER=username,
        MAISON_ADMIN_PASSWORD=password,
        MAISON_PRODUCT_ID=str(product.pk),
        MAISON_IMAGE_PATH=str(settings.BASE_DIR / "assets/editorial/sources/coat.webp"),
    )
    result = subprocess.run(
        ["node", "scripts/qa_admin.mjs"],
        env=environment,
        cwd=settings.BASE_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    product.refresh_from_db()
    assert product.description == "Reviewed by isolated browser QA. Fictional product."
    assert (Path(settings.MEDIA_ROOT) / product.images.first().image.name).exists()
