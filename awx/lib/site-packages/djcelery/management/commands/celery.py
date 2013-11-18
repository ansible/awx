from __future__ import absolute_import, unicode_literals

from celery.bin import celery

from djcelery.app import app
from djcelery.management.base import CeleryCommand

base = celery.CeleryCommand(app=app)


class Command(CeleryCommand):
    """The celery command."""
    help = 'celery commands, see celery help'
    requires_model_validation = True
    options = (CeleryCommand.options
               + base.get_options()
               + base.preload_options)

    def run_from_argv(self, argv):
        argv = self.handle_default_options(argv)
        base.execute_from_commandline(
            ['{0[0]} {0[1]}'.format(argv)] + argv[2:],
        )
