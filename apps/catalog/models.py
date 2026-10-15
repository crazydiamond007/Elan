from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.urls import reverse
from django.utils import timezone

from .images import derivatives, product_image_path, validate_image


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("position", "name")
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:category", args=[self.slug])


class Collection(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("position", "name")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:collection", args=[self.slug])


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=30, unique=True)
    slug = models.SlugField(unique=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("position", "name")

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def public(self):
        variants = Variant.objects.filter(product_id=OuterRef("pk"), is_active=True)
        return self.filter(
            status=Product.Status.PUBLISHED,
            published_at__lte=timezone.now(),
            category__is_active=True,
        ).filter(Exists(variants))

    def for_display(self, variants=None):
        if variants is None:
            variants = Variant.objects.filter(is_active=True)
        return self.select_related("category").prefetch_related(
            Prefetch(
                "variants",
                queryset=variants.select_related("size", "color").order_by(
                    "color__name", "size__position", "size__name"
                ),
                to_attr="display_variants",
            ),
            Prefetch(
                "images",
                queryset=ProductImage.objects.select_related("color"),
                to_attr="display_images",
            ),
        )

    def on_sale(self):
        variants = Variant.objects.filter(
            product_id=OuterRef("pk"),
            is_active=True,
            compare_at_price__gt=models.F("price"),
        )
        return self.filter(Exists(variants))


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    class Department(models.TextChoices):
        WOMEN = "women", "Women"
        MEN = "men", "Men"
        UNISEX = "unisex", "Women & men"
        ACCESSORIES = "accessories", "Accessories"

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField()
    composition = models.TextField(blank=True)
    care = models.TextField(blank=True)
    fit = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    collections = models.ManyToManyField(Collection, blank=True, related_name="products")
    department = models.CharField(max_length=15, choices=Department, default=Department.WOMEN)
    status = models.CharField(max_length=12, choices=Status, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    is_signature = models.BooleanField(
        default=False, help_text="Curated demo placement, not sales data."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ("-published_at", "pk")
        indexes = [
            models.Index(fields=["status", "published_at"]),
            models.Index(fields=["department", "status"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=["draft", "published"]), name="product_valid_status"
            ),
            models.CheckConstraint(
                condition=Q(department__in=["women", "men", "unisex", "accessories"]),
                name="product_valid_department",
            ),
            models.CheckConstraint(
                condition=Q(status="draft") | Q(published_at__isnull=False),
                name="published_product_has_date",
            ),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:product", args=[self.slug])

    def clean(self):
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            raise ValidationError({"published_at": "Set a publication date before publishing."})

    @property
    def primary_image(self):
        return next(iter(self.display_images), None)

    @property
    def price(self):
        return min((variant.price for variant in self.display_variants), default=None)

    @property
    def price_varies(self):
        return len({variant.price for variant in self.display_variants}) > 1

    @property
    def color_names(self):
        return ", ".join(dict.fromkeys(variant.color.name for variant in self.display_variants))

    @property
    def available(self):
        return any(variant.stock > 0 for variant in self.display_variants)


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    size = models.ForeignKey(Size, on_delete=models.PROTECT)
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sku",)
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color", "size"], name="unique_product_option"
            ),
            models.CheckConstraint(condition=Q(price__gt=0), name="variant_positive_price"),
            models.CheckConstraint(condition=Q(stock__gte=0), name="variant_nonnegative_stock"),
            models.CheckConstraint(
                condition=Q(compare_at_price__isnull=True)
                | Q(compare_at_price__gt=models.F("price")),
                name="variant_valid_compare_price",
            ),
        ]

    def __str__(self):
        return f"{self.sku} · {self.color} / {self.size}"

    def clean(self):
        if (
            self.price is not None
            and self.compare_at_price is not None
            and self.compare_at_price <= self.price
        ):
            raise ValidationError(
                {"compare_at_price": "The original price must exceed the sale price."}
            )


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    color = models.ForeignKey(
        Color,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Optional: display this image for a particular colour.",
    )
    image = models.ImageField(
        upload_to=product_image_path, validators=[validate_image], max_length=200
    )
    small = models.ImageField(upload_to=product_image_path, editable=False, max_length=200)
    medium = models.ImageField(upload_to=product_image_path, editable=False, max_length=200)
    alt_text = models.CharField(max_length=250)
    position = models.PositiveSmallIntegerField(default=0)
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    small_width = models.PositiveIntegerField(default=0, editable=False)
    medium_width = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ("position", "pk")

    def __str__(self):
        return self.alt_text

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            generated = derivatives(self.image)
            stored = []
            try:
                for field, (content, width, height) in generated.items():
                    target = getattr(self, field)
                    target.save(content.name, content, save=False)
                    stored.append((target.storage, target.name))
                    if field == "image":
                        self.width, self.height = width, height
                    else:
                        setattr(self, f"{field}_width", width)
                if kwargs.get("update_fields") is not None:
                    kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                        "image",
                        "small",
                        "medium",
                        "width",
                        "height",
                        "small_width",
                        "medium_width",
                    }
                return super().save(*args, **kwargs)
            except Exception:
                for storage, name in stored:
                    storage.delete(name)
                raise
        return super().save(*args, **kwargs)
