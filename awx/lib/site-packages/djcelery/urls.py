"""

URLs defined for celery.

* ``/$task_id/done/``

    URL to :func:`~celery.views.is_successful`.

* ``/$task_id/status/``

    URL  to :func:`~celery.views.task_status`.

"""
from __future__ import absolute_import, unicode_literals

try:
    from django.conf.urls import patterns, url
except ImportError:  # deprecated since Django 1.4
    from django.conf.urls.defaults import patterns, url  # noqa

from . import views

task_pattern = r'(?P<task_id>[\w\d\-\.]+)'

urlpatterns = patterns(
    '',
    url(r'^%s/done/?$' % task_pattern, views.is_task_successful,
        name='celery-is_task_successful'),
    url(r'^%s/status/?$' % task_pattern, views.task_status,
        name='celery-task_status'),
    url(r'^tasks/?$', views.registered_tasks, name='celery-tasks'),
)
