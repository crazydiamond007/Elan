from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("demo/", views.demo_information, name="demo_information"),
    path("collection-preview/", views.collection_preview, name="collection_preview"),
    path(
        "collection-preview/women/",
        views.collection_preview,
        {"department": "women"},
        name="women_preview",
    ),
    path(
        "collection-preview/men/",
        views.collection_preview,
        {"department": "men"},
        name="men_preview",
    ),
    path(
        "collection-preview/accessories/",
        views.collection_preview,
        {"department": "accessories"},
        name="accessories_preview",
    ),
    path("our-story/", views.story, name="story"),
    path("product-care/", views.care, name="care"),
    path("size-guide/", views.size_guide, name="size_guide"),
    path("robots.txt", views.robots, name="robots"),
    path("sitemap.xml", views.sitemap, name="sitemap"),
    path("healthz/", views.health, name="health"),
    path("readyz/", views.ready, name="ready"),
]
