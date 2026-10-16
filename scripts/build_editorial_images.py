"""Build responsive WebP files from versioned editorial masters (no scene alterations)."""

import json
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "assets" / "editorial" / "sources"
OUTPUT = ROOT / "static" / "images" / "editorial"


def save_width(image: Image.Image, name: str, width: int) -> dict[str, str | int]:
    width = min(width, image.width)
    height = round(image.height * width / image.width)
    resized = image.resize((width, height), Image.Resampling.LANCZOS)
    filename = f"{name}-{width}.webp"
    output = OUTPUT / filename
    resized.save(output, "WEBP", quality=78, method=6)
    return {"file": filename, "width": width, "height": height, "bytes": output.stat().st_size}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for source in sorted(SOURCE.glob("*.webp")):
        with Image.open(source) as original:
            image = ImageOps.exif_transpose(original).convert("RGB")
            is_campaign = source.stem in {"hero", "coastal-campaign"}
            if is_campaign:
                widths = (800, 1280, 1600)
            elif source.stem == "catalog-interlude":
                widths = (480, 800, 1200, 1536)
            else:
                widths = (320, 480, 720, 960)
            manifest[source.stem] = [save_width(image, source.stem, width) for width in widths]
            if is_campaign:
                # Art-directed mobile crop keeps both people visible; desktop copy moves below it.
                portrait = ImageOps.fit(
                    image,
                    (800, 1000),
                    Image.Resampling.LANCZOS,
                    centering=(0.78 if source.stem == "hero" else 0.48, 0.5),
                )
                mobile_name = f"{source.stem}-mobile"
                manifest[mobile_name] = [
                    save_width(portrait, mobile_name, width) for width in (480, 640, 800)
                ]
    if not manifest:
        raise SystemExit("No editorial masters found. See docs/asset-licenses.md.")
    (ROOT / "assets" / "editorial" / "image-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    count = sum(len(files) for files in manifest.values())
    total = sum(item["bytes"] for files in manifest.values() for item in files)
    print(f"Built {count} responsive images ({total / 1024:.0f} KiB total).")


if __name__ == "__main__":
    main()
