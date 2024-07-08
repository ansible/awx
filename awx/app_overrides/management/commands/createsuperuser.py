import os

from django.conf import settings
from django.contrib.auth.management.commands.createsuperuser import Command as DjangoCreateSuperUser

from awx.main.tasks.system import periodic_resource_sync
from awx.main.models import User


class Command(DjangoCreateSuperUser):

    def handle(self, *args, **options):
        username = options[User.USERNAME_FIELD]
        if username is None and 'DJANGO_SUPERUSER_USERNAME' in os.environ:
            username = os.environ['DJANGO_SUPERUSER_USERNAME']

        if username and getattr(settings, 'RESOURCE_SERVER', None) and (not User.objects.filter(username=username).exists()):
            periodic_resource_sync()
            existing_user = User.objects.filter(username=username).first()
            if existing_user.exists():
                # user was created by the resource sync
                if not options["interactive"] and ("DJANGO_SUPERUSER_PASSWORD" in os.environ):
                    existing_user.set_password(os.environ["DJANGO_SUPERUSER_PASSWORD"])
                    existing_user.save(update_fields=['password'])

                if options["verbosity"] >= 1:
                    self.stdout.write("Superuser created successfully.")
                return

        return super().handle(*args, **options)
