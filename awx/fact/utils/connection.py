# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings
from mongoengine import connect
from mongoengine.connection import ConnectionError

def test_mongo_connection():
    # Connect to Mongo
    try:
        # Sanity check: If we have intentionally invalid settings, then we
        # know we cannot connect.
        if settings.MONGO_HOST == NotImplemented:
            raise ConnectionError

        # Attempt to connect to the MongoDB database.
        connect(settings.MONGO_DB,
                host=settings.MONGO_HOST,
                port=int(settings.MONGO_PORT),
                username=settings.MONGO_USERNAME,
                password=settings.MONGO_PASSWORD,
                tz_aware=settings.USE_TZ)
        return True
    except ConnectionError:
        return False
    
