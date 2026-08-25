"""
Bootstrap the platform: permission catalogue, default roles and the admin account.

The command is idempotent — run it after every deploy to pick up newly declared
permissions without disturbing roles an administrator has customised.

    python manage.py seed_initial_data
    python manage.py seed_initial_data --demo   # also load sample school data
"""
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.constants import DEFAULT_ROLES, ROLE_SUPER_ADMIN
from apps.accounts.services import create_or_update_admin, sync_permissions, sync_roles


class Command(BaseCommand):
    help = "Seed permissions, roles and the default administrator account."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-admin",
            action="store_true",
            help="Seed permissions and roles only; do not touch the admin account.",
        )
        parser.add_argument(
            "--demo",
            action="store_true",
            help="Additionally load sample classes, subjects, teachers and students.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding The Holy Child School platform"))

        created, updated = sync_permissions()
        self.stdout.write(f"  Permissions : {created} created, {updated} updated")

        created, updated = sync_roles(DEFAULT_ROLES)
        self.stdout.write(f"  Roles       : {created} created, {updated} refreshed")

        if not options["skip_admin"]:
            self._seed_admin()

        if options["demo"]:
            self._seed_demo()

        self.stdout.write(self.style.SUCCESS("Seed complete."))

    # ------------------------------------------------------------------ #
    def _seed_admin(self):
        email = os.getenv("DJANGO_ADMIN_EMAIL")
        password = os.getenv("DJANGO_ADMIN_PASSWORD")
        full_name = os.getenv("DJANGO_ADMIN_NAME", "System Administrator")

        if not email or not password:
            raise CommandError(
                "DJANGO_ADMIN_EMAIL and DJANGO_ADMIN_PASSWORD must be set in the environment.\n"
                "Set them in .env (never commit real credentials) or pass --skip-admin."
            )

        user, was_created = create_or_update_admin(
            email=email, password=password, full_name=full_name, role_slug=ROLE_SUPER_ADMIN
        )
        verb = "created" if was_created else "updated"
        self.stdout.write(f"  Admin       : {user.email} {verb} (role: {user.role_name})")

    def _seed_demo(self):
        from apps.common.demo_data import load_demo_data

        summary = load_demo_data()
        for label, count in summary.items():
            self.stdout.write(f"  Demo {label:<11}: {count}")
