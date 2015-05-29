# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

import logging
import threading
import uuid

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.functional import curry

from awx import __version__ as version
from awx.main.models import ActivityStream, Instance


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
                except IntegrityError:
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


class HAMiddleware(object):
    """A middleware class that checks to see whether the request is being
    served on a secondary instance, and redirects the request back to the
    primary instance if so.
    """
    def process_request(self, request):
        """Process the request, and redirect if this is a request on a
        secondary node.
        """
        # Is this the primary node? If so, we can just return None and be done;
        # we just want normal behavior in this case.
        if Instance.objects.my_role() == 'primary':
            return None

        # Always allow the /ping/ endpoint.
        if request.path.startswith('/api/v1/ping'):
            return None

        # Get the primary instance.
        primary = Instance.objects.primary()

        # If this is a request to /, then we return a special landing page that
        # informs the user that they are on the secondary instance and will
        # be redirected.
        if request.path == '/':
            return TemplateResponse(request, 'ha/redirect.html', {
                'primary': primary,
                'redirect_seconds': 30,
                'version': version,
            })

        # Redirect to the base page of the primary instance.
        return HttpResponseRedirect('http://%s%s' % (primary.hostname, request.path))
