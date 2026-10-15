import re

from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import transaction
from django.urls import reverse
from django.utils import timezone


class ShoppingSessionLockMiddleware:
    """Include SessionMiddleware's read and write in the same PostgreSQL row lock.

    Run outside SessionMiddleware. Product presentation establishes the cookie before
    shoppers submit; existing sessions are serialized across workers and tabs.
    No lock or database access is introduced on ordinary GETs or error pages.
    """

    sync_capable = True
    async_capable = False

    def __init__(self, get_response):
        self.get_response = get_response
        self.paths = {
            reverse(name) for name in ("cart:add", "cart:update", "cart:remove", "checkout:review")
        }

    def __call__(self, request):
        key = request.COOKIES.get(settings.SESSION_COOKIE_NAME, "")
        if (
            request.method != "POST"
            or request.path_info not in self.paths
            or not re.fullmatch(r"[a-z0-9]{32}", key)
        ):
            return self.get_response(request)
        with transaction.atomic():
            Session.objects.select_for_update().filter(
                pk=key, expire_date__gt=timezone.now()
            ).first()
            response = self.get_response(request)
            if response.status_code >= 500:
                transaction.set_rollback(True)
            return response
