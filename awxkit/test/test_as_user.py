from http.cookiejar import Cookie
from unittest import mock

import pytest

from awxkit.api.client import Connection
from awxkit.awx.utils import as_user
from awxkit.config import config


def _make_cookie(name, value, domain='.example.com'):
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=domain,
        domain_specified=True,
        domain_initial_dot=True,
        path='/',
        path_specified=True,
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )


class FakeCookieJar:
    def __init__(self):
        self._cookies = {}

    def __iter__(self):
        return iter(self._cookies.values())

    def get(self, name, default=None):
        c = self._cookies.get(name)
        return c.value if c else default

    def set(self, name, value, domain='.example.com'):
        self._cookies[name] = _make_cookie(name, value, domain)

    def __delitem__(self, name):
        del self._cookies[name]


@pytest.fixture
def connection():
    conn = mock.MagicMock(spec=Connection)
    conn.session = mock.MagicMock()
    conn.session.cookies = FakeCookieJar()
    conn.session_cookie_name = 'sessionid'
    conn.get_session_requirements.return_value = {'next': '/api/controller/'}
    yield conn


class TestAsUserSessionAuth:
    """Tests for as_user() with session-based authentication."""

    def setup_method(self):
        self._orig = config.use_sessions
        config.use_sessions = True

    def teardown_method(self):
        config.use_sessions = self._orig

    def test_swaps_sessionid_cookie(self, connection):
        connection.session.cookies.set('sessionid', 'admin_session')

        with as_user(connection, 'testuser', 'testpass'):
            connection.login.assert_called_once_with('testuser', 'testpass', next='/api/controller/')

        assert connection.session.cookies.get('sessionid') == 'admin_session'

    def test_gateway_sessionid_fallback(self, connection):
        """When session_cookie_name is 'sessionid' but actual cookie is 'gateway_sessionid',
        as_user() should find and swap the gateway cookie."""
        connection.session.cookies.set('gateway_sessionid', 'admin_gw_session')

        with as_user(connection, 'testuser', 'testpass'):
            connection.login.assert_called_once_with('testuser', 'testpass', next='/api/controller/')
            assert connection.session.cookies.get('gateway_sessionid') is None

        assert connection.session.cookies.get('gateway_sessionid') == 'admin_gw_session'

    def test_gateway_fallback_not_triggered_when_sessionid_exists(self, connection):
        """When sessionid cookie exists, gateway_sessionid fallback should not trigger."""
        connection.session.cookies.set('sessionid', 'admin_session')
        connection.session.cookies.set('gateway_sessionid', 'admin_gw_session')

        with as_user(connection, 'testuser', 'testpass'):
            pass

        assert connection.session.cookies.get('sessionid') == 'admin_session'
        assert connection.session.cookies.get('gateway_sessionid') == 'admin_gw_session'

    def test_accepts_user_object(self, connection):
        from awxkit.api import User

        user = mock.MagicMock(spec=User)
        user.username = 'bob'
        user.password = 'secret'
        connection.session.cookies.set('sessionid', 'admin_session')

        with as_user(connection, user):
            connection.login.assert_called_once_with('bob', 'secret', next='/api/controller/')

    def test_restores_gateway_cookie_after_exception(self, connection):
        connection.session.cookies.set('gateway_sessionid', 'admin_gw_session')

        with pytest.raises(RuntimeError):
            with as_user(connection, 'testuser', 'testpass'):
                raise RuntimeError('boom')

        assert connection.session.cookies.get('gateway_sessionid') == 'admin_gw_session'

    def test_no_session_cookie_at_all(self, connection):
        with as_user(connection, 'testuser', 'testpass'):
            connection.login.assert_called_once()


class TestAsUserBasicAuth:
    """Tests for as_user() with basic authentication."""

    def setup_method(self):
        self._orig = config.use_sessions
        config.use_sessions = False

    def teardown_method(self):
        config.use_sessions = self._orig

    def test_swaps_basic_auth(self, connection):
        connection.session.auth = ('admin', 'adminpass')

        with as_user(connection, 'testuser', 'testpass'):
            connection.login.assert_called_once_with('testuser', 'testpass')

        assert connection.session.auth == ('admin', 'adminpass')

    def test_restores_basic_auth_after_exception(self, connection):
        connection.session.auth = ('admin', 'adminpass')

        with pytest.raises(RuntimeError):
            with as_user(connection, 'testuser', 'testpass'):
                raise RuntimeError('boom')

        assert connection.session.auth == ('admin', 'adminpass')
