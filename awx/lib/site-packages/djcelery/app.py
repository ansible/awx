from __future__ import absolute_import, unicode_literals

from celery import current_app


#: The Django-Celery app instance.
app = current_app._get_current_object()
