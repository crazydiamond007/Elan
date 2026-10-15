from django.urls import path

from . import views

app_name = "cart"
urlpatterns = [
    path("bag/", views.bag, name="bag"),
    path("bag/add/", views.add, name="add"),
    path("bag/update/", views.update, name="update"),
    path("bag/remove/", views.remove, name="remove"),
]
