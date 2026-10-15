from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Keep Django authentication behavior while allowing future account extensions."""
