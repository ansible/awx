"""

Start detached worker node from the Django management utility.

"""
from __future__ import absolute_import, unicode_literals

import os
import sys

from celery.bin import celeryd_detach

from djcelery.management.base import CeleryCommand


class Command(CeleryCommand):
    """Run the celery daemon."""
    help = 'Runs a detached Celery worker node.'
    requires_model_validation = True
    options = celeryd_detach.OPTION_LIST

    def run_from_argv(self, argv):

        class detached(celeryd_detach.detached_celeryd):
            execv_argv = [os.path.abspath(sys.argv[0]), 'celery', 'worker']
        detached().execute_from_commandline(argv)
