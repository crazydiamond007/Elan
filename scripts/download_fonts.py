"""Fetch the Latin WOFF2 subsets and their OFL notices for local, CSP-compatible serving."""

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "static" / "fonts"
FAMILIES = {
    "jost": ("Jost:wght@400..600", "jost"),
    "inter": ("Inter:wght@400..600", "inter"),
    "cormorant-garamond": ("Cormorant+Garamond:wght@400..600", "cormorantgaramond"),
    "cormorant-garamond-italic": (
        "Cormorant+Garamond:ital,wght@1,400..600",
        "cormorantgaramond",
    ),
}
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=30) as response:
        content = response.read(1024 * 1024 + 1)
    if len(content) > 1024 * 1024:
        raise ValueError("The font resource exceeded its expected size.")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family", choices=FAMILIES, help="Fetch one family; preserve other assets."
    )
    options = parser.parse_args()
    FONTS.mkdir(parents=True, exist_ok=True)
    manifest_path = FONTS / "font-manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    selected = {options.family: FAMILIES[options.family]} if options.family else FAMILIES
    for name, (family, upstream) in selected.items():
        css_url = f"https://fonts.googleapis.com/css2?family={family}&display=swap"
        css = fetch(css_url).decode()
        # Google Fonts lists the basic Latin subset last; preserve its exact source.
        urls = re.findall(r"src:\s*url\(([^)]+)\)\s*format\(['\"]woff2['\"]\)", css)
        if not urls or urlsplit(urls[-1]).hostname != "fonts.gstatic.com":
            raise ValueError("The expected Google Fonts WOFF2 resource was not found.")
        content = fetch(urls[-1])
        if not content.startswith(b"wOF2"):
            raise ValueError("The downloaded resource is not WOFF2.")
        (FONTS / f"{name}-latin.woff2").write_bytes(content)
        license_url = f"https://raw.githubusercontent.com/google/fonts/main/ofl/{upstream}/OFL.txt"
        license_content = fetch(license_url)
        if b"SIL OPEN FONT LICENSE" not in license_content:
            raise ValueError("The expected font license was not found.")
        (FONTS / f"{name}-OFL.txt").write_bytes(license_content)
        manifest[name] = {
            "css_source": css_url,
            "font_source": urls[-1],
            "license_source": license_url,
            "file": f"{name}-latin.woff2",
            "bytes": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Saved {len(manifest)} self-hosted fonts, license notices and provenance manifest.")


if __name__ == "__main__":
    main()
