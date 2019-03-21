# Python
import pytest
import string
import random

# Django
from django.utils import timezone
from django.test import Client
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.management.base import CommandError

# AWX
from awx.main.management.commands.expire_sessions import Command


@pytest.mark.django_db
class TestExpireSessionsCommand:
    @staticmethod
    def create_and_login_fake_users():
        # We already have Alice and Bob, so we are going to create Charlie and Dylan
        charlie = User.objects.create_user('charlie', 'charlie@email.com', 'pass')
        dylan = User.objects.create_user('dylan', 'dylan@email.com', 'word')
        client_0 = Client()
        client_1 = Client()
        client_0.force_login(charlie, backend=settings.AUTHENTICATION_BACKENDS[0])
        client_1.force_login(dylan, backend=settings.AUTHENTICATION_BACKENDS[0])
        return charlie, dylan

    @staticmethod
    def run_command(username=None):
        command_obj = Command()
        command_obj.handle(user=username)

    def test_expire_all_sessions(self):
        charlie, dylan = self.create_and_login_fake_users()
        self.run_command()
        start = timezone.now()
        sessions = Session.objects.filter(expire_date__gte=start)
        for session in sessions:
            user_id = int(session.get_decoded().get('_auth_user_id'))
            if user_id == charlie.id or user_id == dylan.id:
                self.fail('The user should not have active sessions.')

    def test_non_existing_user(self):
        fake_username = ''
        while fake_username == '' or User.objects.filter(username=fake_username).exists():
            fake_username = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        with pytest.raises(CommandError) as excinfo:
            self.run_command(fake_username)
        assert str(excinfo.value).strip() == 'The user does not exist.'

    def test_expire_one_user(self):
        # alice should be logged out, but bob should not.
        charlie, dylan = self.create_and_login_fake_users()
        self.run_command('charlie')
        start = timezone.now()
        sessions = Session.objects.filter(expire_date__gte=start)
        dylan_still_active = False
        for session in sessions:
            user_id = int(session.get_decoded().get('_auth_user_id'))
            if user_id == charlie.id:
                self.fail('Charlie should not have active sessions.')
            elif user_id == dylan.id:
                dylan_still_active = True
        assert dylan_still_active
