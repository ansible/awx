# Python
import datetime
import pytest
import string
import random
from io import StringIO

# Django
from django.core.management import call_command
from django.core.management.base import CommandError

# AWX
from awx.main.models import RefreshToken
from awx.main.models.oauth import OAuth2AccessToken
from awx.api.versioning import reverse


@pytest.mark.django_db
class TestOAuth2RevokeCommand:

    def test_non_existing_user(self):
        out = StringIO()
        fake_username = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        arg = '--user=' + fake_username
        with pytest.raises(CommandError) as excinfo:
            call_command('revoke_oauth2_tokens', arg, stdout=out)
        assert 'A user with that username does not exist' in str(excinfo.value)
        out.close()

    def test_revoke_all_access_tokens(self, post, admin, alice):
        url = reverse('api:o_auth2_token_list')
        for user in (admin, alice):
            post(
                url,
                {'description': 'test token', 'scope': 'read'},
                user
            )
        assert OAuth2AccessToken.objects.count() == 2
        call_command('revoke_oauth2_tokens')
        assert OAuth2AccessToken.objects.count() == 0

    def test_revoke_access_token_for_user(self, post, admin, alice):
        url = reverse('api:o_auth2_token_list')
        post(
            url,
            {'description': 'test token', 'scope': 'read'},
            alice
        )
        assert OAuth2AccessToken.objects.count() == 1
        call_command('revoke_oauth2_tokens', '--user=admin')
        assert OAuth2AccessToken.objects.count() == 1
        call_command('revoke_oauth2_tokens', '--user=alice')
        assert OAuth2AccessToken.objects.count() == 0

    def test_revoke_all_refresh_tokens(self, post, admin, oauth_application):
        url = reverse('api:o_auth2_token_list')
        post(
            url,
            {
                'description': 'test token for',
                'scope': 'read',
                'application': oauth_application.pk
            },
            admin
        )
        assert OAuth2AccessToken.objects.count() == 1
        assert RefreshToken.objects.count() == 1

        call_command('revoke_oauth2_tokens')
        assert OAuth2AccessToken.objects.count() == 0
        assert RefreshToken.objects.count() == 1
        for r in RefreshToken.objects.all():
            assert r.revoked is None

        call_command('revoke_oauth2_tokens', '--all')
        assert RefreshToken.objects.count() == 1
        for r in RefreshToken.objects.all():
            assert r.revoked is not None
            assert isinstance(r.revoked, datetime.datetime)
