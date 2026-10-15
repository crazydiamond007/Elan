import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal

from django.db.models import Prefetch

from apps.catalog.models import Product, ProductImage, Variant

from .forms import MAX_ID

SESSION_KEY = "cart"
MAX_LINES = 20
MAX_QUANTITY = 10


class CartError(ValueError):
    pass


def read_cart(session):
    raw = session.get(SESSION_KEY, {})
    if not isinstance(raw, dict):
        return {}
    result = {}
    for key, quantity in list(raw.items())[:MAX_LINES]:
        if (
            isinstance(key, str)
            and key.isascii()
            and key.isdecimal()
            and len(key) <= 19
            and 0 < int(key) <= MAX_ID
            and type(quantity) is int
            and 1 <= quantity <= MAX_QUANTITY
        ):
            result[str(int(key))] = quantity
    return result


def eligible_variants():
    return (
        Variant.objects.filter(is_active=True, product__in=Product.objects.public())
        .select_related(
            "product",
            "product__category",
            "size",
            "color",
        )
        .prefetch_related(
            Prefetch("product__images", queryset=ProductImage.objects.order_by("position", "pk"))
        )
    )


@dataclass(frozen=True)
class CartLine:
    variant_id: int
    quantity: int
    variant: Variant | None
    issue: str = ""

    @property
    def name(self):
        return self.variant.product.name if self.variant else "Unavailable piece"

    @property
    def photo(self):
        if self.variant is None:
            return None
        return next(
            (
                image
                for image in self.variant.product.images.all()
                if image.color_id is None or image.color_id == self.variant.color_id
            ),
            None,
        )

    @property
    def total(self):
        return self.variant.price * self.quantity if self.variant else Decimal("0.00")


@dataclass(frozen=True)
class CartSnapshot:
    lines: tuple[CartLine, ...]

    @property
    def subtotal(self):
        return sum((line.total for line in self.lines), Decimal("0.00"))

    @property
    def valid(self):
        return bool(self.lines) and not any(line.issue for line in self.lines)

    @property
    def fingerprint(self):
        contents = [
            (line.variant_id, line.quantity, str(line.variant.price) if line.variant else None)
            for line in self.lines
        ]
        return hashlib.sha256(json.dumps(contents).encode()).hexdigest()


def snapshot(session, *, lock=False):
    quantities = read_cart(session)
    variants = eligible_variants().filter(pk__in=[int(key) for key in quantities])
    if lock:
        variants = variants.select_for_update(of=("self",))
    by_id = {str(variant.pk): variant for variant in variants}
    lines = []
    for key, quantity in sorted(quantities.items(), key=lambda item: int(item[0])):
        variant = by_id.get(key)
        issue = ""
        if variant is None:
            issue = "This piece is no longer available. Remove it to continue."
        elif variant.stock < quantity:
            issue = "The available stock has changed. Reduce the quantity or remove this piece."
        lines.append(CartLine(int(key), quantity, variant, issue))
    return CartSnapshot(tuple(lines))


def write_cart(session, quantities):
    session[SESSION_KEY] = quantities
    session.pop("checkout_review", None)


def change_quantity(session, variant, quantity, *, add=False):
    quantities = read_cart(session)
    key = str(variant.pk)
    quantity += quantities.get(key, 0) if add else 0
    if not 1 <= quantity <= MAX_QUANTITY:
        raise CartError("Choose between 1 and 10 items of a piece.")
    if quantity > variant.stock:
        raise CartError(
            "This quantity is not available. Choose a smaller quantity or another size."
        )
    if key not in quantities and len(quantities) >= MAX_LINES:
        raise CartError("Your demo bag can hold up to 20 different pieces.")
    quantities[key] = quantity
    write_cart(session, quantities)


def remove(session, variant_id):
    quantities = read_cart(session)
    quantities.pop(str(variant_id), None)
    write_cart(session, quantities)
