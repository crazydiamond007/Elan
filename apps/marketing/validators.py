from django.core.exceptions import ValidationError


def validate_demo_email(email):
    domain = email.rsplit("@", 1)[-1].lower()
    if domain not in {"example.com", "example.net", "example.org"} and not domain.endswith(
        (".test", ".invalid")
    ):
        raise ValidationError(
            "Use a fictional address such as guest@example.com. "
            "Real email addresses are not collected."
        )
