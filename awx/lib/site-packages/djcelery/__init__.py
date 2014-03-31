"""Old django celery integration project."""
# :copyright: (c) 2009 - 2012 by Ask Solem.
# :license:   BSD, see LICENSE for more details.
from __future__ import absolute_import, unicode_literals

import os

VERSION = (3, 1, 10)
__version__ = '.'.join(map(str, VERSION[0:3])) + ''.join(VERSION[3:])
__author__ = 'Ask Solem'
__contact__ = 'ask@celeryproject.org'
__homepage__ = 'http://celeryproject.org'
__docformat__ = 'restructuredtext'
__license__ = 'BSD (3 clause)'

# -eof meta-


def setup_loader():
    os.environ.setdefault('CELERY_LOADER', 'djcelery.loaders.DjangoLoader')

from celery import current_app as celery  # noqa
