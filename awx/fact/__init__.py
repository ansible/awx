# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
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
    # Sanity check: If we have intentionally invalid settings, then we
    # know we cannot connect.
    if settings.MONGO_HOST == NotImplemented:
        raise ConnectionError

    # Attempt to connect to the MongoDB database.
    # P.S. Flake8 is terrible. This indentation is consistent with PEP8.
    connect(settings.MONGO_DB,
        host=settings.MONGO_HOST, # noqa
        port=int(settings.MONGO_PORT), # noqa
        username=settings.MONGO_USERNAME, # noqa
        password=settings.MONGO_PASSWORD, # noqa
        tz_aware=settings.USE_TZ, # noqa
    ) # noqa
    register_key_transform(get_db())
except ConnectionError:
    logger.warn('Failed to establish connect to MongoDB "%s"' % (settings.MONGO_DB))
