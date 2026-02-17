from awx.main.models import CredentialType

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Reload CredentialTypes to pull new ones into existing AWX installs.'

    def handle(self, *args, **options):
        try:
            CredentialType.setup_tower_managed_defaults()
        except Exception as e:
            self.stdout.write(f"Ran into exception: {e}, while reloading Credential Types")
        self.stdout.write(self.style.SUCCESS(f"Credential Types have been reloaded."))
