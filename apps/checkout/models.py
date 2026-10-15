from uuid import uuid4

from django.db import models


class DemoReceipt(models.Model):
    """Fictional confirmation snapshot. No payment, customer address or real order."""

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    token = models.UUIDField(unique=True, editable=False)
    session_hash = models.CharField(max_length=64, editable=False)
    lines = models.JSONField(editable=False)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0), name="demo_receipt_nonnegative_total"
            )
        ]

    def __str__(self):
        return self.reference

    @property
    def reference(self):
        return f"DEMO-{str(self.pk)[:8].upper()}"
