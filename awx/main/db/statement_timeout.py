import logging

from django.conf import settings

logger = logging.getLogger('awx.main.db.statement_timeout')


def _get_statement_timeout():
    """Return statement_timeout in ms, or None if not applicable.

    Under uwsgi, derives timeout from harakiri (minus 5s margin so PostgreSQL
    cancels the query before uwsgi kills the worker).  Falls back to the
    DATABASE_STATEMENT_TIMEOUT setting for non-uwsgi deployments.
    """
    try:
        import uwsgi

        harakiri = int(uwsgi.opt.get(b'harakiri', 0))
        if harakiri > 0:
            return (harakiri - 5) * 1000
    except (ImportError, ValueError):
        pass

    return getattr(settings, 'DATABASE_STATEMENT_TIMEOUT', None)


def set_statement_timeout(sender, connection, **kwargs):
    """Django connection_created signal handler."""
    timeout_ms = _get_statement_timeout()
    if timeout_ms is None:
        return
    cursor = connection.cursor()
    cursor.execute("SET statement_timeout = %s", [timeout_ms])
