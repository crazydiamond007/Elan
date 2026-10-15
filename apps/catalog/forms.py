from django import forms

from .images import validate_image
from .models import ProductImage


class CatalogFilterForm(forms.Form):
    q = forms.CharField(
        label="Search pieces",
        max_length=80,
        required=False,
        widget=forms.TextInput(attrs={"type": "search", "placeholder": "Coat, knit, tailoring…"}),
    )
    category = forms.ChoiceField(required=False)
    min_price = forms.DecimalField(
        label="Minimum price (€)", required=False, min_value=0, max_digits=10, decimal_places=2
    )
    max_price = forms.DecimalField(
        label="Maximum price (€)", required=False, min_value=0, max_digits=10, decimal_places=2
    )
    size = forms.ChoiceField(required=False)
    color = forms.ChoiceField(label="Colour", required=False)
    sort = forms.ChoiceField(
        label="Sort by",
        choices=(
            ("newest", "Newest first"),
            ("price-asc", "Price: low to high"),
            ("price-desc", "Price: high to low"),
        ),
        initial="newest",
        required=False,
    )

    def __init__(self, *args, categories, sizes, colors, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        for field, objects, label in (
            ("category", categories, "All categories"),
            ("size", sizes, "All sizes"),
            ("color", colors, "All colours"),
        ):
            self.fields[field].choices = [("", label)] + [(obj.slug, obj.name) for obj in objects]

    def clean(self):
        cleaned = super().clean()
        minimum, maximum = cleaned.get("min_price"), cleaned.get("max_price")
        if minimum is not None and maximum is not None and minimum > maximum:
            self.add_error("max_price", "The maximum price must be at least the minimum price.")
        if hasattr(self.data, "getlist") and any(
            len(self.data.getlist(field)) > 1 for field in self.fields
        ):
            raise forms.ValidationError("Supply each search or filter value only once.")
        return cleaned


class ProductImageForm(forms.ModelForm):
    # Bound the upload before Django's default ImageField performs Pillow verification.
    image = forms.FileField(
        validators=[validate_image],
        help_text="JPEG, PNG or WebP. Maximum 8 MiB and 20 million pixels; no animation.",
        widget=forms.ClearableFileInput(attrs={"accept": ".jpg,.jpeg,.png,.webp"}),
    )

    class Meta:
        model = ProductImage
        fields = ("product", "image", "alt_text", "color", "position")


class SelectionForm(forms.Form):
    color = forms.ChoiceField(label="Colour")
    size = forms.ChoiceField(label="Size")
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={"inputmode": "numeric"}),
    )

    def __init__(self, *args, variants, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        colors = {variant.color.slug: variant.color.name for variant in variants}
        sizes = {variant.size.slug: variant.size.name for variant in variants}
        self.fields["color"].choices = list(colors.items())
        self.fields["size"].choices = list(sizes.items())
        self.variants = variants
        self.variant = None

    def clean(self):
        cleaned = super().clean()
        if "color" in cleaned and "size" in cleaned:
            self.variant = next(
                (
                    variant
                    for variant in self.variants
                    if variant.color.slug == cleaned["color"]
                    and variant.size.slug == cleaned["size"]
                ),
                None,
            )
            if self.variant is None:
                self.add_error(None, "This colour and size combination is unavailable.")
            elif self.variant.stock and cleaned.get("quantity", 0) > self.variant.stock:
                self.add_error("quantity", "This quantity exceeds the available demo stock.")
        return cleaned
