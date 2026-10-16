from urllib.parse import urljoin

from django.conf import settings
from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods, require_safe

from .forms import CatalogFilterForm, SelectionForm
from .models import Category, Collection, Color, Product, Size
from .search import filter_products


@require_safe
def listing(request, section="all", slug=None):
    products = Product.objects.public()
    title = "The collection"
    description = "Quiet silhouettes. Thoughtful textures. A considered wardrobe for everyday life."
    if section in {"women", "men"}:
        products = products.filter(department__in=[section, Product.Department.UNISEX])
        title = section.title()
    elif section == "accessories":
        products = products.filter(department=Product.Department.ACCESSORIES)
        title = "Accessories"
    elif section == "new":
        title = "New arrivals"
    elif section == "sale":
        products = products.on_sale()
        title = "Sale"
        description = "A final opportunity to discover selected pieces from our fictional wardrobe."
    elif section == "category":
        group = get_object_or_404(Category, slug=slug, is_active=True)
        products = products.filter(category=group)
        title, description = group.name, group.description or description
    elif section == "collection":
        group = get_object_or_404(Collection, slug=slug, is_active=True)
        products = products.filter(collections=group)
        title, description = group.name, group.description or description
    categories = list(Category.objects.filter(is_active=True))
    form = CatalogFilterForm(
        request.GET, categories=categories, sizes=Size.objects.all(), colors=Color.objects.all()
    )
    valid = form.is_valid()
    products = (
        filter_products(products, form.cleaned_data, sale=section == "sale")
        if valid
        else products.none()
    )
    raw_page = request.GET.get("page", "1")
    if not raw_page.isascii() or not raw_page.isdecimal() or len(raw_page) > 6:
        raise Http404
    try:
        page = Paginator(products, 12).page(int(raw_page))
    except InvalidPage as error:
        raise Http404 from error
    parameters = request.GET.copy()
    parameters.pop("page", None)
    page_query = parameters.urlencode()
    return render(
        request,
        "catalog/listing.html",
        {
            "page_obj": page,
            "page_numbers": list(
                page.paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)
            ),
            "title": title,
            "description": description,
            "section": section,
            "categories": categories,
            "filter_form": form,
            "page_query": f"{page_query}&" if page_query else "",
            "show_catalog_story": not request.GET and page.paginator.count >= 8,
        },
        status=200 if valid else 400,
    )


@require_safe
def collections(request):
    return render(
        request,
        "catalog/collections.html",
        {
            "collections": Collection.objects.filter(is_active=True),
        },
    )


@require_http_methods(["GET", "HEAD", "POST"])
def product(request, slug):
    piece = get_object_or_404(Product.objects.public().for_display(), slug=slug)
    variants = piece.display_variants
    if not variants:
        raise Http404
    default = next((variant for variant in variants if variant.stock > 0), variants[0])
    data = request.POST if request.method == "POST" else request.GET
    has_selection = request.method == "POST" or any(
        field in data for field in ("color", "size", "quantity")
    )
    form = SelectionForm(
        data if has_selection else None,
        variants=variants,
        initial={
            "color": default.color.slug,
            "size": default.size.slug,
            "quantity": 1,
        },
    )
    selected = default
    valid = True
    if has_selection:
        valid = form.is_valid()
        selected = form.variant if valid else None
    if valid and "cart" not in request.session:
        request.session["cart"] = {}
    images = [
        image
        for image in piece.display_images
        if image.color_id is None or selected is None or image.color_id == selected.color_id
    ]
    styled_ids = list(piece.styled_with.values_list("pk", flat=True))
    related = (
        Product.objects.public().for_display().filter(pk__in=styled_ids)
        if styled_ids
        else Product.objects.public().for_display().filter(category=piece.category)
    )
    related = related.exclude(pk=piece.pk)[:3]
    selection_options = {
        "colors": [
            {"value": value, "label": label} for value, label in form.fields["color"].choices
        ],
        "sizes": [{"value": value, "label": label} for value, label in form.fields["size"].choices],
        "variants": [
            {
                "color": variant.color.slug,
                "size": variant.size.slug,
                "price": f"{variant.price:.2f}",
                "original": f"{variant.compare_at_price:.2f}" if variant.compare_at_price else "",
                "maximum": min(variant.stock, 10),
                "sku": variant.sku,
            }
            for variant in variants
        ],
    }
    return render(
        request,
        "catalog/product.html",
        {
            "piece": piece,
            "selection_form": form,
            "selected": selected,
            "gallery": images,
            "gallery_all": piece.display_images,
            "selection_options": selection_options,
            "related": related,
            "curated_styling": bool(styled_ids),
            "social_title": piece.name + " | MAISON ÉLAN",
            "social_description": piece.description[:160],
            "social_image": urljoin(settings.SITE_URL, images[0].image.url) if images else None,
            "structured_product": piece,
        },
        status=200 if valid else 400,
    )
