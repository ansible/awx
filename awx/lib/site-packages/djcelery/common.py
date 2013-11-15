from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
from functools import wraps

from django.utils import translation


@contextmanager
def respect_language(language):
    """Context manager that changes the current translation language for
    all code inside the following block.

    Can e.g. be used inside tasks like this::

        from celery import task
        from djcelery.common import respect_language

        @task
        def my_task(language=None):
            with respect_language(language):
                pass
    """
    if language:
        prev = translation.get_language()
        translation.activate(language)
        try:
            yield
        finally:
            translation.activate(prev)
    else:
        yield


def respects_language(fun):
    """Decorator for tasks with respect to site's current language.
    You can use this decorator on your tasks together with default @task
    decorator (remember that the task decorator must be applied last).

    See also the with-statement alternative :func:`respect_language`.

    **Example**:

    .. code-block:: python

        @task
        @respects_language
        def my_task()
            # localize something.

    The task will then accept a ``language`` argument that will be
    used to set the language in the task, and the task can thus be
    called like:

    .. code-block:: python

        from django.utils import translation
        from myapp.tasks import my_task

        # Pass the current language on to the task
        my_task.delay(language=translation.get_language())

        # or set the language explicitly
        my_task.delay(language='no.no')

    """

    @wraps(fun)
    def _inner(*args, **kwargs):
        with respect_language(kwargs.pop('language', None)):
            return fun(*args, **kwargs)
    return _inner
