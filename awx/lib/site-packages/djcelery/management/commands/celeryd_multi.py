"""

Utility to manage multiple worker instances.

"""
from __future__ import absolute_import, unicode_literals

from celery.bin import multi

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
        argv.append('--cmd={0[0]} celeryd_detach'.format(argv))
        multi.MultiTool().execute_from_commandline(
            ['{0[0]} {0[1]}'.format(argv)] + argv[2:],
        )
