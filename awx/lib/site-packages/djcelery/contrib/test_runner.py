from __future__ import absolute_import

from uuid import uuid4
from datetime import datetime

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

from celery.task import Task
from djcelery.models import TaskState


USAGE = """\
Custom test runner to allow testing of celery delayed tasks.
"""


class CeleryTestSuiteRunner(DjangoTestSuiteRunner):
    """Django test runner allowing testing of celery delayed tasks.

    All tasks are run locally, not in a worker.

    To use this runner set ``settings.TEST_RUNNER``::

        TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

    """
    def setup_test_environment(self, **kwargs):
        super(CeleryTestSuiteRunner, self).setup_test_environment(**kwargs)
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Issue #75


class CeleryTestSuiteRunnerStoringResult(DjangoTestSuiteRunner):
    """This custom test suite runner make some preliminary
    monkey-patching allowing storing result of Celery task execution
    in ``djcelery.models.TaskState`` model. Tasks run eagerly.

    Exceptions is turned on. If you need to test ``on_failure``
    behavior, you should monkey-patch in your test:
        ``settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = False``

    USAGE:
            In ``settings.py``:
                TEST_RUNNER = 'djcelery.contrib.test_runner.' \
                    'CeleryTestSuiteRunnerStoringResult'

            In ``tests.py``:
                from djcelery.models import TaskState
                TaskState.object.filter(state='SUCCESS', args__contains='test')

    """
    def setup_test_environment(self, **kwargs):
        """Setting up test environment."""

        # Monkey-patch Task.on_success() method
        def on_success_patched(self, retval, task_id, args, kwargs):

            TaskState.objects.create(task_id=uuid4().hex,
                                     state='SUCCESS',
                                     name=self.name,
                                     result=retval,
                                     args=args,
                                     kwargs=kwargs,
                                     tstamp=datetime.now())
        Task.on_success = classmethod(on_success_patched)

        # Monkey-patch Task.on_failure() method
        def on_failure_patched(self, exc, task_id, args, kwargs, einfo):

            TaskState.objects.create(task_id=uuid4().hex,
                                     state='FAILURE',
                                     name=self.name,
                                     result=einfo,
                                     args=args,
                                     kwargs=kwargs,
                                     tstamp=datetime.now())
        Task.on_failure = classmethod(on_failure_patched)

        # Call parent's version
        super(CeleryTestSuiteRunnerStoringResult,
              self).setup_test_environment(**kwargs)

        # Tell celery run tasks synchronously
        settings.CELERY_ALWAYS_EAGER = True
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Issue #75
