from django.contrib import admin

from .models import DemoReceipt


@admin.register(DemoReceipt)
class DemoReceiptAdmin(admin.ModelAdmin):
    list_display = ("reference", "created_at", "subtotal")
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "lines", "subtotal")
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
