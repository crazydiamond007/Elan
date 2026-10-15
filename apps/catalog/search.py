"""Filters and price sorting apply to the same active variant; no raw SQL needed."""

from django.db.models import Exists, F, OuterRef, Q, Subquery

from .models import Variant


def filter_products(products, values, *, sale=False):
    variants = Variant.objects.filter(is_active=True)
    if sale:
        variants = variants.filter(compare_at_price__gt=F("price"))
    for field, lookup in (
        ("size", "size__slug"),
        ("color", "color__slug"),
        ("min_price", "price__gte"),
        ("max_price", "price__lte"),
    ):
        value = values.get(field)
        if value is not None and value != "":
            variants = variants.filter(**{lookup: value})
    if values.get("category"):
        products = products.filter(category__slug=values["category"])
    eligible = variants.filter(product_id=OuterRef("pk"))
    products = products.filter(Exists(eligible))
    if query := values.get("q"):
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Exists(eligible.filter(sku__icontains=query))
        )
    sort = values.get("sort") or "newest"
    if sort in {"price-asc", "price-desc"}:
        products = products.annotate(
            sort_price=Subquery(eligible.order_by("price", "pk").values("price")[:1])
        )
        products = products.order_by("sort_price" if sort == "price-asc" else "-sort_price", "pk")
    return products.for_display(variants=variants)
