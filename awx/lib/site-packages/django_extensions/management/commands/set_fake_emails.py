"""
set_fake_emails.py

    Give all users a new email account. Useful for testing in a
    development environment. As such, this command is only available when
    setting.DEBUG is True.

"""
from optparse import make_option

from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError

DEFAULT_FAKE_EMAIL = '%(username)s@example.com'


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--email', dest='default_email', default=DEFAULT_FAKE_EMAIL,
                    help='Use this as the new email format.'),
        make_option('-a', '--no-admin', action="store_true", dest='no_admin', default=False,
                    help='Do not change administrator accounts'),
        make_option('-s', '--no-staff', action="store_true", dest='no_staff', default=False,
                    help='Do not change staff accounts'),
        make_option('--include', dest='include_regexp', default=None,
                    help='Include usernames matching this regexp.'),
        make_option('--exclude', dest='exclude_regexp', default=None,
                    help='Exclude usernames matching this regexp.'),
        make_option('--include-groups', dest='include_groups', default=None,
                    help='Include users matching this group. (use comma seperation for multiple groups)'),
        make_option('--exclude-groups', dest='exclude_groups', default=None,
                    help='Exclude users matching this group. (use comma seperation for multiple groups)'),
    )
    help = '''DEBUG only: give all users a new email based on their account data ("%s" by default). Possible parameters are: username, first_name, last_name''' % (DEFAULT_FAKE_EMAIL, )
    requires_model_validation = False

    def handle_noargs(self, **options):
        if not settings.DEBUG:
            raise CommandError('Only available in debug mode')

        try:
            from django.contrib.auth import get_user_model  # Django 1.5
        except ImportError:
            from django_extensions.future_1_5 import get_user_model
        from django.contrib.auth.models import Group
        email = options.get('default_email', DEFAULT_FAKE_EMAIL)
        include_regexp = options.get('include_regexp', None)
        exclude_regexp = options.get('exclude_regexp', None)
        include_groups = options.get('include_groups', None)
        exclude_groups = options.get('exclude_groups', None)
        no_admin = options.get('no_admin', False)
        no_staff = options.get('no_staff', False)

        User = get_user_model()
        users = User.objects.all()
        if no_admin:
            users = users.exclude(is_superuser=True)
        if no_staff:
            users = users.exclude(is_staff=True)
        if exclude_groups:
            groups = Group.objects.filter(name__in=exclude_groups.split(","))
            if groups:
                users = users.exclude(groups__in=groups)
            else:
                raise CommandError("No group matches filter: %s" % exclude_groups)
        if include_groups:
            groups = Group.objects.filter(name__in=include_groups.split(","))
            if groups:
                users = users.filter(groups__in=groups)
            else:
                raise CommandError("No groups matches filter: %s" % include_groups)
        if exclude_regexp:
            users = users.exclude(username__regex=exclude_regexp)
        if include_regexp:
            users = users.filter(username__regex=include_regexp)
        for user in users:
            user.email = email % {'username': user.username,
                                  'first_name': user.first_name,
                                  'last_name': user.last_name}
            user.save()
        print('Changed %d emails' % users.count())
