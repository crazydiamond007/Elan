from django.db import models

from .validators import validate_demo_email


class DemoSignup(models.Model):
    email = models.EmailField(unique=True, validators=[validate_demo_email])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        validate_demo_email(self.email)
        return super().save(*args, **kwargs)

    def clean(self):
        self.email = self.email.strip().lower()
