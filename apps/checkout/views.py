from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_safe

from apps.cart.services import CartError, snapshot
from apps.core.rate_limits import allow_request

from .forms import DemoCheckoutForm
from .models import DemoReceipt
from .services import complete, owner_hash, review


@never_cache
@require_http_methods(["GET", "HEAD", "POST"])
def checkout(request):
    bag = snapshot(request.session)
    error, status = "", 200
    form = DemoCheckoutForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if not allow_request(request, "checkout", limit=10, seconds=600):
            response = render(
                request,
                "checkout/review.html",
                {
                    "bag": bag,
                    "form": form,
                    "error": "Please wait ten minutes before trying demo checkout again.",
                },
                status=429,
            )
            response["Retry-After"] = "600"
            return response
        if form.is_valid():
            try:
                receipt = complete(request.session, form.cleaned_data["token"])
            except CartError as failure:
                error, status = str(failure), 409
            else:
                return redirect("checkout:confirmation", receipt_id=receipt.pk)
        else:
            status = 400
    if bag.valid:
        reviewed = review(request.session, bag)
        # A refreshed review replaces stale submitted tokens and keeps errors visible.
        form.initial["token"] = reviewed["token"]
        if form.is_bound:
            rebound = form.data.copy()
            rebound["token"] = reviewed["token"]
            form.data = rebound
        if request.method == "POST" and status == 409:
            form = DemoCheckoutForm(initial={"token": reviewed["token"]})
    return render(
        request, "checkout/review.html", {"bag": bag, "form": form, "error": error}, status=status
    )


@never_cache
@require_safe
def confirmation(request, receipt_id):
    receipt = get_object_or_404(
        DemoReceipt, pk=receipt_id, session_hash=owner_hash(request.session)
    )
    return render(request, "checkout/confirmation.html", {"receipt": receipt})
