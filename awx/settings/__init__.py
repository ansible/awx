# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

from django.conf import settings
from mongoengine import connect
from mongoengine.connection import get_db, ConnectionError
from awx.main.dbtransform import register_key_transform
import logging

logger = logging.getLogger('awx.settings.__init__')

try:
    connect(settings.MONGO_DB)
    register_key_transform(get_db())
except ConnectionError:
    logger.warn('Failed to establish connect to MongDB "%s"' % (settings.MONGO_DB))
