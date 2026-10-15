from django.db import models


class RateLimitBucket(models.Model):
    """Expiring, HMAC-keyed counters; do not store raw client IPs."""

    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)

    def __str__(self):
        return f"Rate counter {self.key[:12]}"
