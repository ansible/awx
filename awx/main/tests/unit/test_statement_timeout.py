import types
from unittest import mock

import pytest

from awx.main.db import statement_timeout as st_mod


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the module-level cache between tests."""
    st_mod._cached_timeout_ms = st_mod._UNSET
    yield
    st_mod._cached_timeout_ms = st_mod._UNSET


class TestGetStatementTimeout:
    def test_derives_from_uwsgi_harakiri(self):
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'115'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            assert st_mod._get_statement_timeout() == (115 - 5) * 1000

    def test_returns_none_without_uwsgi_or_setting(self):
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            assert st_mod._get_statement_timeout() is None

    def test_falls_back_to_setting(self, settings):
        settings.DATABASE_STATEMENT_TIMEOUT = 60000
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            assert st_mod._get_statement_timeout() == 60000

    def test_uwsgi_takes_precedence_over_setting(self, settings):
        settings.DATABASE_STATEMENT_TIMEOUT = 60000
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'115'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            assert st_mod._get_statement_timeout() == 110000

    def test_uwsgi_harakiri_zero_falls_back_to_setting(self, settings):
        settings.DATABASE_STATEMENT_TIMEOUT = 90000
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'0'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            assert st_mod._get_statement_timeout() == 90000

    def test_caches_result(self):
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'115'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            first = st_mod._get_statement_timeout()
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            second = st_mod._get_statement_timeout()
        assert first == second == 110000


class TestSetStatementTimeout:
    def test_executes_set_when_timeout_available(self):
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'115'}
        mock_cursor = mock.MagicMock()
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            st_mod.set_statement_timeout(sender=None, connection=mock_connection)
        mock_cursor.execute.assert_called_once_with("SET statement_timeout = %s", [110000])

    def test_does_nothing_when_no_timeout(self):
        mock_connection = mock.MagicMock()
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            st_mod.set_statement_timeout(sender=None, connection=mock_connection)
        mock_connection.cursor.assert_not_called()
