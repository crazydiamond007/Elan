from django.contrib import admin

from .admin_forms import ProductAdminForm, VariantAdminForm, VariantInlineFormSet
from .forms import ProductImageForm
from .models import Category, Collection, Color, Product, ProductImage, Size, Variant


@admin.register(Category, Collection)
class GroupingAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "position")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Color, Size)
class OptionAdmin(admin.ModelAdmin):
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class VariantInline(admin.TabularInline):
    model = Variant
    form = VariantAdminForm
    formset = VariantInlineFormSet
    extra = 0
    autocomplete_fields = ("color", "size")
    fields = ("sku", "color", "size", "price", "compare_at_price", "stock", "is_active")


class ImageInline(admin.StackedInline):
    model = ProductImage
    form = ProductImageForm
    extra = 0
    autocomplete_fields = ("color",)
    fields = ("image", "alt_text", "color", "position")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "department", "category", "status", "published_at", "is_featured")
    list_filter = ("status", "department", "category", "collections", "is_featured", "is_signature")
    search_fields = ("name", "slug", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (VariantInline, ImageInline)
    date_hierarchy = "published_at"
    list_select_related = ("category",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "description")}),
        (
            "Product details",
            {
                "fields": (
                    "composition",
                    "care",
                    "fit",
                    "department",
                    "category",
                    "collections",
                    "styled_with",
                )
            },
        ),
        (
            "Publication & merchandising",
            {"fields": ("status", "published_at", "is_featured", "is_signature")},
        ),
        ("Record", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "color", "size", "price", "stock", "is_active")
    list_filter = ("is_active", "color", "size", "product__department")
    search_fields = ("sku", "product__name")
    autocomplete_fields = ("product", "color", "size")
    list_select_related = ("product", "color", "size")
    readonly_fields = ("updated_at",)
    list_editable = ("stock", "is_active")


@admin.register(ProductImage)
class ImageAdmin(admin.ModelAdmin):
    form = ProductImageForm
    list_display = ("product", "alt_text", "color", "position")
    search_fields = ("product__name", "alt_text")
    autocomplete_fields = ("product", "color")
    list_select_related = ("product", "color")
    fields = ("product", "image", "alt_text", "color", "position", "width", "height")
    readonly_fields = ("width", "height")
