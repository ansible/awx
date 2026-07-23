import logging

from django.conf import settings

logger = logging.getLogger('awx.main.db.statement_timeout')

_UNSET = object()
_cached_timeout_ms = _UNSET


def _get_statement_timeout():
    """Return statement_timeout in ms, or None if not applicable.

    Under uwsgi, derives timeout from harakiri (minus 5s margin so PostgreSQL
    cancels the query before uwsgi kills the worker).  Falls back to the
    DATABASE_STATEMENT_TIMEOUT setting for non-uwsgi deployments.
    """
    global _cached_timeout_ms
    if _cached_timeout_ms is not _UNSET:
        return _cached_timeout_ms

    timeout_ms = None
    try:
        import uwsgi

        harakiri = int(uwsgi.opt.get(b'harakiri', 0))
        if harakiri > 0:
            timeout_ms = (harakiri - 5) * 1000
    except (ImportError, ValueError):
        pass

    if timeout_ms is None:
        timeout_ms = getattr(settings, 'DATABASE_STATEMENT_TIMEOUT', None)

    _cached_timeout_ms = timeout_ms
    if timeout_ms is not None:
        logger.info('Setting statement_timeout=%dms on new database connections', timeout_ms)
    return timeout_ms


def set_statement_timeout(sender, connection, **kwargs):
    """Django connection_created signal handler."""
    timeout_ms = _get_statement_timeout()
    if timeout_ms is None:
        return
    cursor = connection.cursor()
    cursor.execute("SET statement_timeout = %s", [timeout_ms])
