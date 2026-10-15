from django.shortcuts import render
from django.utils.cache import add_never_cache_headers
from django.utils.deprecation import MiddlewareMixin

from apps.core.rate_limits import allow_request


class AdminLoginRateLimitMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != "POST" or request.resolver_match.view_name != "admin:login":
            return None
        if allow_request(request, "admin-login", limit=10, seconds=600):
            return None
        response = render(request, "errors/rate_limited.html", status=429)
        response["Retry-After"] = "600"
        add_never_cache_headers(response)
        return response
