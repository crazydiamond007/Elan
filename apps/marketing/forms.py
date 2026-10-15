from django import forms

from .validators import validate_demo_email


class NewsletterForm(forms.Form):
    email = forms.EmailField(
        label="Demo email address",
        max_length=254,
        widget=forms.EmailInput(attrs={"placeholder": "guest@example.com", "autocomplete": "off"}),
    )

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        validate_demo_email(email)
        return email
