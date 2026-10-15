from django.contrib import admin

from .models import DemoSignup


@admin.register(DemoSignup)
class DemoSignupAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")
    search_fields = ("email",)
    readonly_fields = ("created_at",)
