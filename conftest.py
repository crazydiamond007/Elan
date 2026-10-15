from io import BytesIO

import pytest
from django.core.management import call_command
from PIL import Image


@pytest.fixture
def catalog_data(db, settings, tmp_path):
    """Exercise the real seed command using small, valid test-only image masters."""
    original_base = settings.BASE_DIR
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.BASE_DIR = tmp_path
    sources = tmp_path / "assets/editorial/sources"
    sources.mkdir(parents=True)
    for name in ("coat", "knit", "trousers", "bag"):
        image = Image.new("RGB", (120, 160), "#C6B8A8")
        output = BytesIO()
        image.save(output, "WEBP")
        (sources / f"{name}.webp").write_bytes(output.getvalue())
    call_command("seed_catalog", verbosity=0)
    settings.BASE_DIR = original_base
