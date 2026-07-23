import types
from unittest import mock

from awx.main.db.statement_timeout import _get_statement_timeout, set_statement_timeout


class TestGetStatementTimeout:
    def test_derives_from_uwsgi_harakiri(self):
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'115'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            assert _get_statement_timeout() == (115 - 5) * 1000

    def test_returns_none_without_uwsgi_or_setting(self):
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            assert _get_statement_timeout() is None

    def test_falls_back_to_setting(self, settings):
        settings.DATABASE_STATEMENT_TIMEOUT = 60000
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            assert _get_statement_timeout() == 60000

    def test_uwsgi_takes_precedence_over_setting(self, settings):
        settings.DATABASE_STATEMENT_TIMEOUT = 60000
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'115'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            assert _get_statement_timeout() == 110000

    def test_uwsgi_harakiri_zero_falls_back_to_setting(self, settings):
        settings.DATABASE_STATEMENT_TIMEOUT = 90000
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'0'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            assert _get_statement_timeout() == 90000

    def test_uwsgi_harakiri_very_low_clamps_to_one_second(self):
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'1'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            assert _get_statement_timeout() == 1000

    def test_uwsgi_harakiri_midrange_uses_proportional_margin(self):
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'30'}
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            # margin = min(5, max(1, int(30*0.1))) = 3 → timeout = 27s
            assert _get_statement_timeout() == 27000


class TestSetStatementTimeout:
    def test_executes_set_when_timeout_available(self):
        fake_uwsgi = types.ModuleType('uwsgi')
        fake_uwsgi.opt = {b'harakiri': b'115'}
        mock_cursor = mock.MagicMock()
        mock_connection = mock.MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        with mock.patch.dict('sys.modules', {'uwsgi': fake_uwsgi}):
            set_statement_timeout(sender=None, connection=mock_connection)
        mock_cursor.execute.assert_called_once_with("SET statement_timeout = %s", [110000])

    def test_does_nothing_when_no_timeout(self):
        mock_connection = mock.MagicMock()
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            set_statement_timeout(sender=None, connection=mock_connection)
        mock_connection.cursor.assert_not_called()
