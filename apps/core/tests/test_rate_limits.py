from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.db import close_old_connections
from django.test import RequestFactory
from django.utils import timezone

from apps.core.models import RateLimitBucket
from apps.core.rate_limits import allow_request

pytestmark = pytest.mark.django_db


def test_rate_counters_store_hashes_and_expire_without_resetting_active_limits():
    request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.1")
    assert allow_request(request, "test", limit=1, seconds=600)
    assert not allow_request(request, "test", limit=1, seconds=600)
    counter = RateLimitBucket.objects.get()
    assert "192.0.2.1" not in counter.key
    assert len(counter.key) == 64
    expired = RateLimitBucket.objects.create(
        key="expired", count=1, expires_at=timezone.now() - timedelta(seconds=1)
    )
    call_command("prune_rate_limits", stdout=StringIO())
    assert not RateLimitBucket.objects.filter(pk=expired.pk).exists()
    assert RateLimitBucket.objects.filter(pk=counter.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_requests_cannot_exceed_the_shared_counter_limit():
    def request_once(_):
        close_old_connections()
        try:
            request = RequestFactory().post("/", REMOTE_ADDR="192.0.2.10")
            return allow_request(request, "concurrent", limit=3, seconds=600)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=5) as pool:
        assert sum(pool.map(request_once, range(10))) == 3
    assert RateLimitBucket.objects.get().count == 3
