from django import forms


class DemoCheckoutForm(forms.Form):
    token = forms.UUIDField(widget=forms.HiddenInput)
    acknowledge = forms.BooleanField(
        label="I understand this is a demonstration. No payment or real order will be made."
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
