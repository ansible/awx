import pytest
from datetime import timedelta
import re

from django.utils.timezone import now as tz_now
from django.test.utils import override_settings
from awx.api.versioning import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.models import Session
from django.contrib.auth import SESSION_KEY

from awx.main.models import AuthToken, User, UserSessionMembership


@override_settings(AUTH_TOKEN_PER_USER=3)
@pytest.mark.django_db
def test_get_tokens_over_limit():
    now = tz_now()
    # Times are relative to now
    # (key, created on in seconds , expiration in seconds)
    test_data = [
        # a is implicitly expired
        ("a", -1000, -10),
        # b's are invalid due to session limit of 3
        ("b", -100, 60),
        ("bb", -100, 60),
        ("c", -90, 70),
        ("d", -80, 80),
        ("e", -70, 90),
    ]
    user = User.objects.create_superuser('admin', 'foo@bar.com', 'password')
    for key, t_create, t_expire in test_data:
        AuthToken.objects.create(
            user=user,
            key=key,
            request_hash='this_is_a_hash',
            created=now + timedelta(seconds=t_create),
            expires=now + timedelta(seconds=t_expire),
        )
    invalid_tokens = AuthToken.get_tokens_over_limit(user, now=now)
    invalid_keys = [x.key for x in invalid_tokens]
    assert len(invalid_keys) == 2
    assert 'b' in invalid_keys
    assert 'bb' in invalid_keys


class AlwaysPassBackend(object):

    user = None

    def authenticate(self, **credentials):
        return AlwaysPassBackend.user

    @classmethod
    def get_backend_path(cls):
        return '{}.{}'.format(cls.__module__, cls.__name__)


@pytest.mark.django_db
def test_session_create_delete(admin, post, delete):
    AlwaysPassBackend.user = admin
    with override_settings(AUTHENTICATION_BACKENDS=(AlwaysPassBackend.get_backend_path(),),
                           SESSION_COOKIE_NAME='session_id'):
        response = post(reverse('api:user_session_view'),
                        data={'username': admin.username, 'password': admin.password},
                        expect=201, middleware=SessionMiddleware())
        assert 'session_id' in response.cookies
        session_key = re.findall(r'session_id=[a-zA-z0-9]+',
                                 str(response.cookies['session_id']))[0][len('session_id=') :]
        session = Session.objects.get(session_key=session_key)
        assert int(session.get_decoded()[SESSION_KEY]) == admin.pk
        response = delete(reverse('api:user_session_view'), middleware=SessionMiddleware(),
                          cookies={'session_id': session_key}, expect=204)
        assert not Session.objects.filter(session_key=session_key).exists()


@pytest.mark.django_db
def test_session_overlimit(admin, post):
    AlwaysPassBackend.user = admin
    with override_settings(AUTHENTICATION_BACKENDS=(AlwaysPassBackend.get_backend_path(),),
                           SESSION_COOKIE_NAME='session_id', AUTH_TOKEN_PER_USER=3):
        sessions_to_deprecate = []
        for _ in range(5):
            response = post(reverse('api:user_session_view'),
                            data={'username': admin.username, 'password': admin.password},
                            expect=201, middleware=SessionMiddleware())
            session_key = re.findall(
                r'session_id=[a-zA-z0-9]+',
                str(response.cookies['session_id'])
            )[0][len('session_id=') :]
            sessions_to_deprecate.append(Session.objects.get(session_key=session_key))
        sessions_to_deprecate[0].expire_date = tz_now() - timedelta(seconds=1000)
        sessions_to_deprecate[0].save()
        sessions_overlimit = [x.session for x in UserSessionMembership.get_memberships_over_limit(admin)]
        assert sessions_to_deprecate[0] not in sessions_overlimit
        assert sessions_to_deprecate[1] in sessions_overlimit
        for session in sessions_to_deprecate[2 :]:
            assert session not in sessions_overlimit
