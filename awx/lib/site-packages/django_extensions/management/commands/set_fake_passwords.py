"""
set_fake_passwords.py

    Reset all user passwords to a common value. Useful for testing in a
    development environment. As such, this command is only available when
    setting.DEBUG is True.

"""
from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError

DEFAULT_FAKE_PASSWORD = 'password'


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--prompt', dest='prompt_passwd', default=False, action='store_true',
                    help='Prompts for the new password to apply to all users'),
        make_option('--password', dest='default_passwd', default=DEFAULT_FAKE_PASSWORD,
                    help='Use this as default password.'),
    )
    help = 'DEBUG only: sets all user passwords to a common value ("%s" by default)' % (DEFAULT_FAKE_PASSWORD, )
    requires_model_validation = False

    def handle_noargs(self, **options):
        if not settings.DEBUG:
            raise CommandError('Only available in debug mode')

        try:
            from django.contrib.auth import get_user_model  # Django 1.5
        except ImportError:
            from django_extensions.future_1_5 import get_user_model

        if options.get('prompt_passwd', False):
            from getpass import getpass
            passwd = getpass('Password: ')
            if not passwd:
                raise CommandError('You must enter a valid password')
        else:
            passwd = options.get('default_passwd', DEFAULT_FAKE_PASSWORD)

        User = get_user_model()
        user = User()
        user.set_password(passwd)
        count = User.objects.all().update(password=user.password)

        print('Reset %d passwords' % count)
