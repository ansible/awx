import pytest
from datetime import timedelta
import re

from django.utils.timezone import now as tz_now
from django.test.utils import override_settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.models import Session
from django.contrib.auth import SESSION_KEY

from awx.main.models import UserSessionMembership
from awx.api.versioning import reverse


class AlwaysPassBackend(object):

    user = None

    def authenticate(self, **credentials):
        return AlwaysPassBackend.user

    @classmethod
    def get_backend_path(cls):
        return '{}.{}'.format(cls.__module__, cls.__name__)


@pytest.mark.django_db
@pytest.mark.parametrize('accept, status', [
    ['*/*', 200],
    ['text/html', 200],
    ['application/json', 406]
])
def test_login_json_not_allowed(get, accept, status):
    get(
        '/api/login/',
        HTTP_ACCEPT=accept,
        expect=status
    )


@pytest.mark.skip(reason="Needs Update - CA")
@pytest.mark.django_db
def test_session_create_delete(admin, post, get):
    AlwaysPassBackend.user = admin
    with override_settings(
        AUTHENTICATION_BACKENDS=(AlwaysPassBackend.get_backend_path(),),
        SESSION_COOKIE_NAME='session_id'
    ):
        response = post(
            '/api/login/',
            data={'username': admin.username, 'password': admin.password, 'next': '/api/'},
            expect=302, middleware=SessionMiddleware(), format='multipart'
        )
        assert 'session_id' in response.cookies
        session_key = re.findall(r'session_id=[a-zA-z0-9]+',
                                 str(response.cookies['session_id']))[0][len('session_id=') :]
        session = Session.objects.get(session_key=session_key)
        assert int(session.get_decoded()[SESSION_KEY]) == admin.pk
        response = get(
            '/api/logout/', middleware=SessionMiddleware(),
            cookies={'session_id': session_key}, expect=302
        )
        assert not Session.objects.filter(session_key=session_key).exists()


@pytest.mark.skip(reason="Needs Update - CA")
@pytest.mark.django_db
def test_session_overlimit(admin, post):
    AlwaysPassBackend.user = admin
    with override_settings(
        AUTHENTICATION_BACKENDS=(AlwaysPassBackend.get_backend_path(),),
        SESSION_COOKIE_NAME='session_id', SESSIONS_PER_USER=3
    ):
        sessions_to_deprecate = []
        for _ in range(5):
            response = post(
                '/api/login/',
                data={'username': admin.username, 'password': admin.password, 'next': '/api/'},
                expect=302, middleware=SessionMiddleware(), format='multipart'
            )
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


@pytest.mark.skip(reason="Needs Update - CA")
@pytest.mark.django_db
def test_password_update_clears_sessions(admin, alice, post, patch):
    AlwaysPassBackend.user = alice
    with override_settings(
        AUTHENTICATION_BACKENDS=(AlwaysPassBackend.get_backend_path(),),
        SESSION_COOKIE_NAME='session_id'
    ):
        response = post(
            '/api/login/',
            data={'username': alice.username, 'password': alice.password, 'next': '/api/'},
            expect=302, middleware=SessionMiddleware(), format='multipart'
        )
        session_key = re.findall(
            r'session_id=[a-zA-z0-9]+',
            str(response.cookies['session_id'])
        )[0][len('session_id=') :]
        assert Session.objects.filter(session_key=session_key).exists()
        patch(
            reverse('api:user_detail', kwargs={'pk': alice.pk}), admin,
            data={'password': 'new_password'}, expect=200
        )
        assert not Session.objects.filter(session_key=session_key).exists()
