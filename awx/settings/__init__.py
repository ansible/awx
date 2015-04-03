# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

from django.conf import settings
from mongoengine import connect
from mongoengine.connection import get_db
from awx.main.dbtransform import register_key_transform

connect(settings.MONGO_DB)
register_key_transform(get_db())