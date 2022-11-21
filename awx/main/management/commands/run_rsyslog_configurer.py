import logging

from django.core.management.base import BaseCommand
from awx.main.dispatch import pg_bus_conn
from awx.main.utils.external_logging import reconfigure_rsyslog

logger = logging.getLogger('awx.main.rsyslog_configurer')


class Command(BaseCommand):
    """
    Rsyslog Configurer
    Runs as a management command and starts rsyslog configurer daemon. Daemon listens
    for pg_notify then calls reconfigure_rsyslog
    """

    help = 'Launch the rsyslog_configurer daemon'

    def handle(self, *arg, **options):
        try:
            with pg_bus_conn(new_connection=True) as conn:
                conn.listen("rsyslog_configurer")
                for e in conn.events(yield_timeouts=True):
                    if e is not None:
                        reconfigure_rsyslog()
        except Exception:
            # Log unanticipated exception in addition to writing to stderr to get timestamps and other metadata
            logger.exception('Encountered unhandled error in rsyslog_configurer main loop')
            raise
