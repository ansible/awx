"""

Utility to manage multiple :program:`celeryd` instances.

"""
from __future__ import absolute_import

from celery.bin import celeryd_multi

from djcelery.management.base import CeleryCommand


class Command(CeleryCommand):
    """Run the celery daemon."""
    args = '[name1, [name2, [...]> [worker options]'
    help = 'Manage multiple Celery worker nodes.'
    requires_model_validation = True
    options = ()
    keep_base_opts = True

    def run_from_argv(self, argv):
        argv = self.handle_default_options(argv)
        argv.append('--cmd=%s celeryd_detach' % (argv[0], ))
        celeryd_multi.MultiTool().execute_from_commandline(
            ['%s %s' % (argv[0], argv[1])] + argv[2:],
        )
