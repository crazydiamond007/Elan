from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control


class DemoRobotsMiddleware:
    """Keep every demo response unindexed, including admin, errors and static assets."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        if response.get("Content-Type", "").startswith("text/html"):
            patch_cache_control(response, private=True, no_cache=True)
        return response
