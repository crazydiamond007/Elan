from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.catalog.models import Category, Collection, Product


class PageSitemap(Sitemap):
    def items(self):
        return [
            "core:home",
            "core:story",
            "core:care",
            "core:size_guide",
            "core:demo_information",
            "catalog:all",
            "catalog:new",
            "catalog:women",
            "catalog:men",
            "catalog:accessories",
            "catalog:sale",
            "catalog:collections",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    def items(self):
        return Product.objects.public().only("slug", "updated_at")

    def lastmod(self, item):
        return item.updated_at


class CategorySitemap(Sitemap):
    def items(self):
        return Category.objects.filter(is_active=True)


class CollectionSitemap(Sitemap):
    def items(self):
        return Collection.objects.filter(is_active=True)


SITEMAPS = {
    "pages": PageSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "collections": CollectionSitemap,
}
