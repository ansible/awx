from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import argparse


class Command(BaseCommand):
    """enable or disable authentication system"""

    def add_arguments(self, parser):
        """
        This adds the --enable functionality to the command using argparse to allow either enable or no-enable
        """
        parser.add_argument('--enable', action=argparse.BooleanOptionalAction, help='to disable local auth --no-enable to enable --enable')

    def _enable_disable_auth(self, enable):
        """
        this method allows the disabling or enabling of local authenication based on the argument passed into the parser
        if no arguments throw a command error, if --enable set the DISABLE_LOCAL_AUTH to False
        if --no-enable set to True. Realizing that the flag is counterintuitive to what is expected.
        """
        if enable is None:
            raise CommandError('Please pass --enable flag to allow local auth or --no-enable flag to disable local auth')
        if enable:
            settings.DISABLE_LOCAL_AUTH = False
            print("Setting has changed to {} allowing local authentication".format(settings.DISABLE_LOCAL_AUTH))
            return

        settings.DISABLE_LOCAL_AUTH = True
        print("Setting has changed to {} disallowing local authentication".format(settings.DISABLE_LOCAL_AUTH))

    def handle(self, **options):
        self._enable_disable_auth(options.get('enable'))
