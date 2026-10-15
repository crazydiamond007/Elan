from datetime import UTC, datetime

from django.db.models import F
from django.utils.crypto import salted_hmac

from .models import RateLimitBucket


def allow_request(request, scope, *, limit, seconds):
    """Fixed-window PostgreSQL counter; conditional updates enforce the limit atomically.

    Use REMOTE_ADDR, never an untrusted forwarding header. Proxy deployments must review
    client-address handling. Infrastructure controls are still necessary against distributed abuse.
    """
    now = datetime.now(UTC)
    window = int(now.timestamp()) // seconds
    client = getattr(request, "client_ip", request.META.get("REMOTE_ADDR", "unknown"))
    identity = f"{scope}:{client}:{window}"
    key = salted_hmac("maison.rate-limit", identity, algorithm="sha256").hexdigest()
    RateLimitBucket.objects.get_or_create(
        key=key,
        defaults={
            "expires_at": datetime.fromtimestamp((window + 1) * seconds, UTC),
        },
    )
    return bool(
        RateLimitBucket.objects.filter(key=key, count__lt=limit).update(count=F("count") + 1)
    )
