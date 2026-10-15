from django import forms

MAX_ID = 9223372036854775807


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=10)


class AddForm(QuantityForm):
    product_slug = forms.SlugField(max_length=160)
    color = forms.SlugField(max_length=50)
    size = forms.SlugField(max_length=50)


class UpdateForm(QuantityForm):
    variant_id = forms.IntegerField(min_value=1, max_value=MAX_ID)


class RemoveForm(forms.Form):
    variant_id = forms.IntegerField(min_value=1, max_value=MAX_ID)
