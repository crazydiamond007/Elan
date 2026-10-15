from uuid import uuid4

from django.db import transaction
from django.utils.crypto import salted_hmac

from apps.cart import services as cart

from .models import DemoReceipt


def owner_hash(session):
    return salted_hmac(
        "maison.demo-receipt", session.session_key or "", algorithm="sha256"
    ).hexdigest()


def review(session, bag):
    previous = session.get("checkout_review", {})
    if not isinstance(previous, dict) or previous.get("fingerprint") != bag.fingerprint:
        previous = {"token": str(uuid4()), "fingerprint": bag.fingerprint}
        session["checkout_review"] = previous
    return previous


def complete(session, token):
    """Revalidate under variant locks; a unique token makes repeated submissions idempotent."""
    if not session.session_key:
        raise cart.CartError("Start demo checkout from your bag in this browser.")
    session_hash = owner_hash(session)
    existing = DemoReceipt.objects.filter(token=token, session_hash=session_hash).first()
    if existing:
        return existing
    reviewed = session.get("checkout_review", {})
    if not isinstance(reviewed, dict) or reviewed.get("token") != str(token):
        raise cart.CartError("This checkout has expired. Review your bag and try again.")
    with transaction.atomic():
        bag = cart.snapshot(session, lock=True)
        if not bag.valid:
            raise cart.CartError(
                "Your bag has changed or contains an unavailable piece. "
                "Update it before continuing."
            )
        if reviewed.get("fingerprint") != bag.fingerprint:
            raise cart.CartError(
                "A price or quantity has changed. Review the updated summary before confirming."
            )
        lines = [
            {
                "name": line.name,
                "sku": line.variant.sku,
                "color": line.variant.color.name,
                "size": line.variant.size.name,
                "quantity": line.quantity,
                "unit_price": str(line.variant.price),
                "total": str(line.total),
            }
            for line in bag.lines
        ]
        receipt, _ = DemoReceipt.objects.get_or_create(
            token=token,
            defaults={
                "session_hash": session_hash,
                "lines": lines,
                "subtotal": bag.subtotal,
            },
        )
        if receipt.session_hash != session_hash:
            raise cart.CartError(
                "This checkout is unavailable. Start a new checkout from your bag."
            )
    cart.write_cart(session, {})
    session["demo_receipt"] = str(receipt.pk)
    return receipt
