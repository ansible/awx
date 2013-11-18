from __future__ import absolute_import, unicode_literals

import sys
import threading

from celery.bin import events

from django.core.management.commands import runserver

from djcelery.app import app
from djcelery.management.base import CeleryCommand

ev = events.events(app=app)


class WebserverThread(threading.Thread):

    def __init__(self, addrport='', *args, **options):
        threading.Thread.__init__(self)
        self.addrport = addrport
        self.args = args
        self.options = options

    def run(self):
        options = dict(self.options, use_reloader=False)
        command = runserver.Command()
        # see http://code.djangoproject.com/changeset/13319
        command.stdout, command.stderr = sys.stdout, sys.stderr
        command.handle(self.addrport, *self.args, **options)


class Command(CeleryCommand):
    """Run the celery curses event viewer."""
    args = '[optional port number, or ipaddr:port]'
    options = (runserver.Command.option_list
               + ev.get_options()
               + ev.preload_options)
    help = 'Starts Django Admin instance and celerycam in the same process.'
    # see http://code.djangoproject.com/changeset/13319.
    stdout, stderr = sys.stdout, sys.stderr

    def handle(self, addrport='', *args, **options):
        """Handle the management command."""
        server = WebserverThread(addrport, *args, **options)
        server.start()
        options['camera'] = 'djcelery.snapshot.Camera'
        options['prog_name'] = 'djcelerymon'
        ev.run(*args, **options)
