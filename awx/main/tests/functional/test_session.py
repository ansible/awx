from importlib import import_module
import pytest

from django.conf import settings
from django.test.utils import override_settings
from django.contrib.sessions.models import Session
from django.contrib.auth import SESSION_KEY
from unittest import mock


class AlwaysPassBackend(object):
    user = None

    def authenticate(self, **credentials):
        return AlwaysPassBackend.user

    @classmethod
    def get_backend_path(cls):
        return '{}.{}'.format(cls.__module__, cls.__name__)


@pytest.mark.django_db
@pytest.mark.parametrize('accept, status', [['*/*', 200], ['text/html', 200], ['application/json', 406]])
def test_login_json_not_allowed(get, accept, status):
    get('/api/login/', HTTP_ACCEPT=accept, expect=status)


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_sessions_unlimited(emit, admin):
    assert Session.objects.count() == 0
    for i in range(5):
        store = import_module(settings.SESSION_ENGINE).SessionStore()
        store.create_model_instance({SESSION_KEY: admin.pk}).save()
        assert Session.objects.count() == i + 1
    assert emit.call_count == 0


@pytest.mark.django_db
@mock.patch('awx.main.consumers.emit_channel_notification')
def test_session_overlimit(emit, admin, alice):
    # If SESSIONS_PER_USER=3, only persist the three most recently created sessions
    assert Session.objects.count() == 0
    with override_settings(SESSIONS_PER_USER=3):
        created = []
        for i in range(5):
            store = import_module(settings.SESSION_ENGINE).SessionStore()
            session = store.create_model_instance({SESSION_KEY: admin.pk})
            session.save()
            created.append(session.session_key)
    assert [s.pk for s in Session.objects.all()] == created[-3:]
    assert emit.call_count == 2  # 2 of 5 sessions were evicted
    emit.assert_called_with('control-limit_reached_{}'.format(admin.pk), {'reason': 'limit_reached', 'group_name': 'control'})

    # Allow sessions for a different user to be saved
    store = import_module(settings.SESSION_ENGINE).SessionStore()
    store.create_model_instance({SESSION_KEY: alice.pk}).save()
    assert Session.objects.count() == 4
