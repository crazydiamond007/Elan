from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from apps.core.rate_limits import allow_request

from .forms import NewsletterForm
from .models import DemoSignup


@never_cache
@require_http_methods(["GET", "HEAD", "POST"])
def newsletter(request):
    form = NewsletterForm(request.POST if request.method == "POST" else None)
    status, error = 200, ""
    if request.method == "POST":
        if not allow_request(request, "newsletter", limit=5, seconds=600):
            response = render(
                request,
                "marketing/newsletter.html",
                {
                    "form": form,
                    "error": "Please wait ten minutes before trying the newsletter demo again.",
                },
                status=429,
            )
            response["Retry-After"] = "600"
            return response
        if form.is_valid():
            DemoSignup.objects.get_or_create(email=form.cleaned_data["email"])
            messages.success(request, "Your demo signup was saved locally. No email will be sent.")
            return redirect("marketing:newsletter")
        else:
            status = 400
    return render(
        request,
        "marketing/newsletter.html",
        {"form": form, "error": error},
        status=status,
    )
