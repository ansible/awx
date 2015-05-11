# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

from __future__ import absolute_import

import logging
from django.conf import settings

from mongoengine import connect
from mongoengine.connection import get_db, ConnectionError
from .utils.dbtransform import register_key_transform

logger = logging.getLogger('awx.fact')

# Connect to Mongo
try:
    connect(settings.MONGO_DB, tz_aware=settings.USE_TZ)
    register_key_transform(get_db())
except ConnectionError:
    logger.warn('Failed to establish connect to MongoDB "%s"' % (settings.MONGO_DB))
