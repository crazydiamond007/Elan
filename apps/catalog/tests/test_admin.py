import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from apps.catalog.models import Product, Variant

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "model", ["product", "category", "collection", "variant", "productimage", "color", "size"]
)
def test_catalog_admin_requires_staff_and_model_permissions(client, django_user_model, model):
    url = reverse(f"admin:catalog_{model}_changelist")
    assert client.get(url).status_code == 302
    user = django_user_model.objects.create_user(username="staff", is_staff=True)
    client.force_login(user)
    assert client.get(url).status_code == 403
    user.user_permissions.add(
        Permission.objects.get(codename=f"view_{model}", content_type__app_label="catalog")
    )
    assert client.get(url).status_code == 200
    assert client.get(reverse(f"admin:catalog_{model}_add")).status_code == 403


def test_superuser_can_manage_catalog_and_inline_records(client, django_user_model, catalog_data):
    user = django_user_model.objects.create_superuser(
        username="catalog-admin", password="test-only-strong-password"
    )
    client.force_login(user)
    product = Product.objects.first()
    response = client.get(reverse("admin:catalog_product_change", args=[product.pk]))
    assert response.status_code == 200
    assert b"variants-TOTAL_FORMS" in response.content
    assert b"images-TOTAL_FORMS" in response.content
    assert b"Publication &amp; merchandising" in response.content


def test_catalog_admin_mutations_require_csrf(client, django_user_model, catalog_data):
    from django.test import Client

    secure_client = Client(enforce_csrf_checks=True)
    user = django_user_model.objects.create_superuser(
        username="csrf-admin", password="test-only-strong-password"
    )
    secure_client.force_login(user)
    variant = Variant.objects.first()
    response = secure_client.post(
        reverse("admin:catalog_variant_change", args=[variant.pk]), {"stock": 99}
    )
    assert response.status_code == 403
    old_stock = variant.stock
    variant.refresh_from_db()
    assert variant.stock == old_stock
