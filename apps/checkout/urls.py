from django.urls import path

from . import views

app_name = "checkout"
urlpatterns = [
    path("checkout/", views.checkout, name="review"),
    path("checkout/confirmation/<uuid:receipt_id>/", views.confirmation, name="confirmation"),
]
