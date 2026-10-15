"""Original Phase 3 capsule, retained as input to the non-destructive seed command.

Storefront views use the catalog database exclusively. These constants never supply
authoritative prices, inventory or publication decisions to customer views.
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PreviewPiece:
    slug: str
    name: str
    price: Decimal
    image: str
    color: str
    description: str
    departments: tuple[str, ...]
    composition: str = ""


PIECES = (
    PreviewPiece(
        "sculpted-coat",
        "The Sculpted Wool Coat",
        Decimal("320.00"),
        "coat",
        "Charcoal",
        "A generous silhouette, softened shoulders and a clean double-breasted front. "
        "An imagined outer layer for the quieter days of autumn.",
        ("women",),
    ),
    PreviewPiece(
        "fine-wool-knit",
        "The Fine Wool Knit",
        Decimal("145.00"),
        "knit",
        "Ivory",
        "A considered crew neckline and an easy, relaxed shape. An imagined fine knit "
        "to layer, repeat and make your own.",
        ("women", "men"),
    ),
    PreviewPiece(
        "pleated-trouser",
        "The Pleated Trouser",
        Decimal("185.00"),
        "trousers",
        "Sand",
        "Soft front pleats and a fluid, wide leg. An imagined balance between the "
        "precision of tailoring and the ease of everyday dressing.",
        ("women", "men"),
    ),
    PreviewPiece(
        "everyday-tote",
        "The Everyday Tote",
        Decimal("220.00"),
        "bag",
        "Black",
        "Quiet lines, long handles and a supple shape. An imagined companion for "
        "the things you carry through the day.",
        ("accessories",),
    ),
)

DEPARTMENTS = {"women": "Women", "men": "Men", "accessories": "Accessories"}

# Optional, image-matched expansion. Only the seed command consumes these records.
EXPANDED_PIECES = (
    PreviewPiece(
        "wool-overshirt",
        "The Wool Overshirt",
        Decimal("195.00"),
        "overshirt",
        "Chocolate",
        "Soft wool, considered pockets and an easy straight silhouette. An imagined layer "
        "that moves naturally between a shirt and a jacket.",
        ("men",),
        "Imagined fine wool with plain tonal buttons.",
    ),
    PreviewPiece(
        "linen-shirt",
        "The Linen Shirt",
        Decimal("115.00"),
        "linen-shirt",
        "Ivory",
        "A relaxed collar and the quiet texture of linen. An imagined everyday shirt "
        "with room to move and a gently curved hem.",
        ("men",),
        "Imagined woven linen with tonal buttons.",
    ),
    PreviewPiece(
        "tailored-blazer",
        "The Soft Tailored Blazer",
        Decimal("265.00"),
        "tailored-blazer",
        "Taupe",
        "Gentle structure, a single button and precise lapels. An imagined interpretation "
        "of tailoring for a less formal rhythm.",
        ("women",),
        "Imagined wool-rich tailoring with a smooth lining.",
    ),
    PreviewPiece(
        "merino-cardigan",
        "The Merino Cardigan",
        Decimal("165.00"),
        "merino-cardigan",
        "Oatmeal",
        "Fine knit, a clean V neckline and useful pockets. An imagined cardigan "
        "to reach for as the light changes.",
        ("men",),
        "Imagined fine-gauge merino wool.",
    ),
    PreviewPiece(
        "silk-midi-dress",
        "The Silk Midi Dress",
        Decimal("240.00"),
        "silk-dress",
        "Black",
        "A quiet neckline and a fluid midi silhouette. An imagined silk dress "
        "with a softly defined waist and subtle movement.",
        ("women",),
        "Imagined matte silk with a lightweight lining.",
    ),
    PreviewPiece(
        "straight-wool-trouser",
        "The Straight Wool Trouser",
        Decimal("175.00"),
        "navy-trousers",
        "Navy",
        "A precise crease, soft front pleats and a straight leg. An imagined "
        "foundation for a considered daily wardrobe.",
        ("men",),
        "Imagined fine woven wool.",
    ),
    PreviewPiece(
        "twill-blouson",
        "The Twill Blouson",
        Decimal("210.00"),
        "zip-jacket",
        "Olive",
        "A neat collar, clean zip and understated pockets. An imagined cotton "
        "layer with softly structured proportions.",
        ("men",),
        "Imagined cotton twill and lightweight textile lining.",
    ),
    PreviewPiece(
        "pleated-midi-skirt",
        "The Pleated Midi Skirt",
        Decimal("155.00"),
        "pleated-skirt",
        "Slate",
        "Fine pleats and a clean waistband create quiet movement. An imagined "
        "midi skirt for simple, thoughtful combinations.",
        ("women",),
        "Imagined wool-blend pleated fabric.",
    ),
    PreviewPiece(
        "merino-turtleneck",
        "The Merino Turtleneck",
        Decimal("135.00"),
        "merino-top",
        "Burgundy",
        "A folded collar and fine ribbed edges. An imagined merino layer "
        "that brings a deeper note to the neutral wardrobe.",
        ("women",),
        "Imagined fine-gauge merino wool.",
    ),
    PreviewPiece(
        "brushed-wool-scarf",
        "The Brushed Wool Scarf",
        Decimal("85.00"),
        "wool-scarf",
        "Camel",
        "Soft brushed wool, generous proportions and a quiet fringed edge. "
        "An imagined finishing layer for cooler days.",
        ("accessories",),
        "Imagined brushed wool.",
    ),
)
