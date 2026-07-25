from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extends Django's default user with the fields a booking platform needs."""

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_space_owner = models.BooleanField(
        default=False,
        help_text="Designates whether this user can manage/list coworking spaces.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username
