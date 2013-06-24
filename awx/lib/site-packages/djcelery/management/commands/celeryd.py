"""

Start the celery daemon from the Django management command.

"""
from __future__ import absolute_import

from celery.bin import celeryd

from djcelery.app import app
from djcelery.management.base import CeleryCommand

worker = celeryd.WorkerCommand(app=app)


class Command(CeleryCommand):
    """Run the celery daemon."""
    help = 'Old alias to the "celery worker" command.'
    requires_model_validation = True
    options = (CeleryCommand.options
               + worker.get_options()
               + worker.preload_options)

    def handle(self, *args, **options):
        worker.run(*args, **options)
