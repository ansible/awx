from django.core.management.base import BaseCommand, CommandError
try:
    from django.contrib.auth import get_user_model  # Django 1.5
except ImportError:
    from django_extensions.future_1_5 import get_user_model
from django.contrib.sessions.models import Session
import re

SESSION_RE = re.compile("^[0-9a-f]{20,40}$")


class Command(BaseCommand):
    help = ("print the user information for the provided session key. "
            "this is very helpful when trying to track down the person who "
            "experienced a site crash.")
    args = "session_key"
    label = 'session key for the user'

    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("extra arguments supplied")
        if len(args) < 1:
            raise CommandError("session_key argument missing")
        key = args[0].lower()
        if not SESSION_RE.match(key):
            raise CommandError("malformed session key")
        try:
            session = Session.objects.get(pk=key)
        except Session.DoesNotExist:
            print("Session Key does not exist. Expired?")
            return

        data = session.get_decoded()
        print('Session to Expire: %s' % session.expire_date)
        print('Raw Data: %s' % data)
        uid = data.get('_auth_user_id', None)
        if uid is None:
            print('No user associated with session')
            return
        print("User id: %s" % uid)
        User = get_user_model()
        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            print("No user associated with that id.")
            return
        for key in ['username', 'email', 'first_name', 'last_name']:
            print("%s: %s" % (key, getattr(user, key)))
