from django.conf import settings
from django.contrib.auth.management.commands.createsuperuser import Command as DjangoCreateSuperUser


class Command(DjangoCreateSuperUser):

    def handle(self, *args, **options):
        if getattr(settings, 'settings.RESOURCE_SERVER', None):
            pass  # TODO run sync
        return super().handle(*args, **options)
