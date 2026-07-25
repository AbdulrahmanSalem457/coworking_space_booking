import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Creates the project's one real superuser from the ADMIN_USERNAME / "
        "ADMIN_EMAIL / ADMIN_PASSWORD variables in backend/.env. Safe to run "
        "more than once — does nothing if that user already exists."
    )

    def handle(self, *args, **options):
        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")

        if not all([username, email, password]):
            raise CommandError(
                "Set ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD in backend/.env first."
            )

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"[SKIP] Admin account '{username}' already exists")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"[OK] Created admin account '{username}'"))
