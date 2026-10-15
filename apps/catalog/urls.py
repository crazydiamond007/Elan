from django.urls import path

from . import views

app_name = "catalog"
urlpatterns = [
    path("shop/", views.listing, name="all"),
    path("shop/new-arrivals/", views.listing, {"section": "new"}, name="new"),
    path("shop/women/", views.listing, {"section": "women"}, name="women"),
    path("shop/men/", views.listing, {"section": "men"}, name="men"),
    path("shop/accessories/", views.listing, {"section": "accessories"}, name="accessories"),
    path("shop/sale/", views.listing, {"section": "sale"}, name="sale"),
    path("shop/category/<slug:slug>/", views.listing, {"section": "category"}, name="category"),
    path("collections/", views.collections, name="collections"),
    path("collections/<slug:slug>/", views.listing, {"section": "collection"}, name="collection"),
    path("products/<slug:slug>/", views.product, name="product"),
]
