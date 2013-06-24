"""

Celery manamagent and monitoring utility.

"""
from __future__ import absolute_import

from celery.bin.celeryctl import celeryctl, Command as _Command

from djcelery import __version__
from djcelery.app import app
from djcelery.management.base import CeleryCommand

# Django hijacks the version output and prints its version before our
# version. So display the names of the products so the output is sensible.
_Command.version = 'celery %s\ndjango-celery %s' % (_Command.version,
                                                    __version__)


class Command(CeleryCommand):
    """Run the celery control utility."""
    help = 'Old alias to the "celery" command'
    keep_base_opts = False

    def run_from_argv(self, argv):
        util = celeryctl(app=app)

        util.execute_from_commandline(self.handle_default_options(argv)[1:])
