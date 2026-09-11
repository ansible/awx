import types
from unittest import mock

from awx.settings.functions import merge_statement_timeout

PG_ENGINE = "django.db.backends.postgresql"
SQLITE_ENGINE = "django.db.backends.sqlite3"


def _make_settings(engine=PG_ENGINE, timeout=None, existing_options=""):
    """Build a dict that quacks like DYNACONF.get() for merge_statement_timeout."""
    data = {"DATABASES__default__ENGINE": engine}
    if timeout is not None:
        data["DATABASE_STATEMENT_TIMEOUT"] = timeout
    if existing_options:
        data["DATABASES__default__OPTIONS__options"] = existing_options
    return data


def _fake_uwsgi(harakiri):
    mod = types.ModuleType('uwsgi')
    mod.opt = {b'harakiri': str(harakiri).encode()}
    return mod


class TestMergeStatementTimeout:
    def test_derives_from_uwsgi_harakiri(self):
        settings = _make_settings()
        with mock.patch.dict('sys.modules', {'uwsgi': _fake_uwsgi(115)}):
            result = merge_statement_timeout(settings)
        assert result == {"DATABASES__default__OPTIONS__options": "-c statement_timeout=110000"}

    def test_returns_empty_without_uwsgi_or_setting(self):
        settings = _make_settings()
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            result = merge_statement_timeout(settings)
        assert result == {}

    def test_falls_back_to_setting(self):
        settings = _make_settings(timeout=60000)
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            result = merge_statement_timeout(settings)
        assert result == {"DATABASES__default__OPTIONS__options": "-c statement_timeout=60000"}

    def test_uwsgi_takes_precedence_over_setting(self):
        settings = _make_settings(timeout=60000)
        with mock.patch.dict('sys.modules', {'uwsgi': _fake_uwsgi(115)}):
            result = merge_statement_timeout(settings)
        assert result == {"DATABASES__default__OPTIONS__options": "-c statement_timeout=110000"}

    def test_harakiri_zero_falls_back_to_setting(self):
        settings = _make_settings(timeout=90000)
        with mock.patch.dict('sys.modules', {'uwsgi': _fake_uwsgi(0)}):
            result = merge_statement_timeout(settings)
        assert result == {"DATABASES__default__OPTIONS__options": "-c statement_timeout=90000"}

    def test_harakiri_very_low_clamps_to_one_second(self):
        settings = _make_settings()
        with mock.patch.dict('sys.modules', {'uwsgi': _fake_uwsgi(1)}):
            result = merge_statement_timeout(settings)
        assert result == {"DATABASES__default__OPTIONS__options": "-c statement_timeout=1000"}

    def test_harakiri_midrange_uses_proportional_margin(self):
        settings = _make_settings()
        with mock.patch.dict('sys.modules', {'uwsgi': _fake_uwsgi(30)}):
            # margin = min(5, max(1, int(30*0.1))) = 3 → timeout = 27s
            result = merge_statement_timeout(settings)
        assert result == {"DATABASES__default__OPTIONS__options": "-c statement_timeout=27000"}

    def test_skips_sqlite(self):
        settings = _make_settings(engine=SQLITE_ENGINE, timeout=60000)
        result = merge_statement_timeout(settings)
        assert result == {}

    def test_appends_to_existing_options(self):
        settings = _make_settings(timeout=60000, existing_options="-c lock_timeout=5000")
        with mock.patch.dict('sys.modules', {'uwsgi': None}):
            result = merge_statement_timeout(settings)
        assert result == {"DATABASES__default__OPTIONS__options": "-c lock_timeout=5000 -c statement_timeout=60000"}
