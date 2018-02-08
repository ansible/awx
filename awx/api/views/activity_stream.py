# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# AWX
from awx.api.generics import (
    SimpleListAPIView,
    RetrieveAPIView,
)
from awx.api.views.mixins import ActivityStreamEnforcementMixin
from awx.api.serializers import ActivityStreamSerializer
from awx.main.models import ActivityStream


logger = logging.getLogger('awx.api.views')


class ActivityStreamList(ActivityStreamEnforcementMixin, SimpleListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    new_in_145 = True


class ActivityStreamDetail(ActivityStreamEnforcementMixin, RetrieveAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    new_in_145 = True
