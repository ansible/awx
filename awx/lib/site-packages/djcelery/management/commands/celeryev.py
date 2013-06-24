"""

Curses Celery Event Viewer.

"""
from __future__ import absolute_import

from celery.bin import celeryev

from djcelery.app import app
from djcelery.management.base import CeleryCommand

ev = celeryev.EvCommand(app=app)

SS_TRANSPORTS = ['amqplib', 'kombu.transport.pyamqplib',
                 'redis', 'kombu.transport.pyredis',
                 'pika', 'kombu.transport.pypika']

SS_COMPAT = """
ERROR: Snapshots not currently supported by %s transport.
Please use one of: %s
"""


class Command(CeleryCommand):
    """Run the celery curses event viewer."""
    options = (CeleryCommand.options
               + ev.get_options()
               + ev.preload_options)
    help = 'Old alias to the "celery events command"'

    def handle(self, *args, **options):
        """Handle the management command."""
        transport = app.conf.BROKER_TRANSPORT or 'amqplib'
        if options['camera']:
            if transport not in SS_TRANSPORTS:
                self.die(
                    SS_COMPAT % (
                        transport,
                        ', '.join(t for t in SS_TRANSPORTS if '.' not in t)),
                )
        ev.run(*args, **options)
