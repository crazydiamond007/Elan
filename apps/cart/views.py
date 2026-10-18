from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_safe

from apps.core.rate_limits import allow_request

from . import services
from .forms import AddForm, RemoveForm, UpdateForm


def bag_response(request, *, error="", status=200):
    return render(
        request,
        "cart/bag.html",
        {"bag": services.snapshot(request.session), "error": error},
        status=status,
    )


def rate_response(request):
    if allow_request(request, "cart", limit=60, seconds=60):
        return None
    response = bag_response(
        request, error="Please wait a minute before changing your demo bag again.", status=429
    )
    response["Retry-After"] = "60"
    return response


@never_cache
@require_safe
def bag(request):
    return bag_response(request)


@never_cache
@require_POST
def add(request):
    if limited := rate_response(request):
        return limited
    form = AddForm(request.POST)
    if not form.is_valid():
        return bag_response(
            request,
            error="Choose a valid colour, size and quantity before adding a piece.",
            status=400,
        )
    data = form.cleaned_data
    variant = (
        services.eligible_variants()
        .filter(
            product__slug=data["product_slug"], color__slug=data["color"], size__slug=data["size"]
        )
        .first()
    )
    if variant is None:
        return bag_response(
            request, error="This piece or option is no longer available.", status=409
        )
    try:
        services.change_quantity(request.session, variant, data["quantity"], add=True)
    except services.CartError as error:
        return bag_response(request, error=str(error), status=409)
    messages.success(
        request,
        f"Added to your demo bag: {variant.product.name} · "
        f"{variant.color.name} / {variant.size.name} · Quantity {data['quantity']}.",
        extra_tags="bag-added",
    )
    return redirect("cart:bag")


@never_cache
@require_POST
def update(request):
    if limited := rate_response(request):
        return limited
    form = UpdateForm(request.POST)
    if not form.is_valid():
        return bag_response(
            request, error="Choose a whole-number quantity between 1 and 10.", status=400
        )
    data = form.cleaned_data
    if str(data["variant_id"]) not in services.read_cart(request.session):
        return bag_response(request, error="This piece is not in your bag.", status=400)
    variant = services.eligible_variants().filter(pk=data["variant_id"]).first()
    if variant is None:
        return bag_response(
            request, error="This piece is no longer available. Remove it to continue.", status=409
        )
    try:
        services.change_quantity(request.session, variant, data["quantity"])
    except services.CartError as error:
        return bag_response(request, error=str(error), status=409)
    messages.success(request, "Your demo bag has been updated.")
    return redirect("cart:bag")


@never_cache
@require_POST
def remove(request):
    if limited := rate_response(request):
        return limited
    form = RemoveForm(request.POST)
    if not form.is_valid():
        return bag_response(request, error="Choose a valid piece to remove.", status=400)
    services.remove(request.session, form.cleaned_data["variant_id"])
    messages.success(request, "The piece has been removed from your demo bag.")
    return redirect("cart:bag")
