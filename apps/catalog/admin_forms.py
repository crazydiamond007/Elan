from django import forms
from django.forms.models import BaseInlineFormSet

from .models import Product, Variant


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "slug",
            "description",
            "composition",
            "care",
            "fit",
            "department",
            "category",
            "collections",
            "styled_with",
            "status",
            "published_at",
            "is_featured",
            "is_signature",
        )
        widgets = {
            "collections": forms.CheckboxSelectMultiple,
            "styled_with": forms.CheckboxSelectMultiple,
            "published_at": forms.SplitDateTimeWidget(
                date_format="%Y-%m-%d",
                time_format="%H:%M:%S",
                date_attrs={"type": "date"},
                time_attrs={"type": "time", "step": "1"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["styled_with"].queryset = Product.objects.exclude(pk=self.instance.pk)
        widget = self.fields["published_at"].widget
        if hasattr(widget, "widgets"):
            for control, label in zip(
                widget.widgets, ("Publication date", "Publication time"), strict=True
            ):
                control.attrs["aria-label"] = label


class VariantAdminForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ("sku", "color", "size", "price", "compare_at_price", "stock", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["aria-label"] = (
                f"{field.label} for {self.instance.sku or 'new variant'}"
            )


class VariantInlineFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if "DELETE" in form.fields:
            form.fields["DELETE"].widget.attrs["aria-label"] = (
                f"Remove variant {form.instance.sku or index}"
            )
