# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.db.models.signals import pre_save, post_save
from django.db import IntegrityError
from django.utils.functional import curry
from awx.main.models import ActivityStream, AuthToken
import json
import threading
import uuid
import urllib2

import logging
logger = logging.getLogger('awx.main.middleware')

class ActivityStreamMiddleware(threading.local):

    def __init__(self):
        self.disp_uid = None
        self.instance_ids = []

    def process_request(self, request):
        if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated():
            user = request.user
        else:
            user = None

        set_actor = curry(self.set_actor, user)
        self.disp_uid = str(uuid.uuid1())
        self.instance_ids = []
        post_save.connect(set_actor, sender=ActivityStream, dispatch_uid=self.disp_uid, weak=False)

    def process_response(self, request, response):
        drf_request = getattr(request, 'drf_request', None)
        drf_user = getattr(drf_request, 'user', None)
        if self.disp_uid is not None:
            post_save.disconnect(dispatch_uid=self.disp_uid)

        for instance in ActivityStream.objects.filter(id__in=self.instance_ids):
            if drf_user and drf_user.id:
                instance.actor = drf_user
                try:
                    instance.save(update_fields=['actor'])
                except IntegrityError, e:
                    logger.debug("Integrity Error saving Activity Stream instance for id : " + str(instance.id))
            # else:
            #     obj1_type_actual = instance.object1_type.split(".")[-1]
            #     if obj1_type_actual in ("InventoryUpdate", "ProjectUpdate", "Job") and instance.id is not None:
            #         instance.delete()

        self.instance_ids = []
        return response

    def set_actor(self, user, sender, instance, **kwargs):
        if sender == ActivityStream:
            if isinstance(user, User) and instance.actor is None:
                instance.actor = user
                instance.save(update_fields=['actor'])
            else:
                if instance.id not in self.instance_ids:
                    self.instance_ids.append(instance.id)
