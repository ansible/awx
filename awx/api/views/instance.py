# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import logging

# Django
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.main.access import get_user_queryset
from awx.api.generics import (
    ListAPIView,
    RetrieveAPIView,
    SubListAPIView,
)
from awx.api.serializers import (
    InstanceSerializer,
    InstanceGroupSerializer,
    UnifiedJobSerializer,
)
from awx.main.models import (
    Instance,
    InstanceGroup,
    UnifiedJob,
)

logger = logging.getLogger('awx.api.views')


class InstanceList(ListAPIView):

    view_name = _("Instances")
    model = Instance
    serializer_class = InstanceSerializer
    new_in_320 = True


class InstanceDetail(RetrieveAPIView):

    view_name = _("Instance Detail")
    model = Instance
    serializer_class = InstanceSerializer
    new_in_320 = True


class InstanceUnifiedJobsList(SubListAPIView):

    view_name = _("Instance Running Jobs")
    model = UnifiedJob
    serializer_class = UnifiedJobSerializer
    parent_model = Instance
    new_in_320 = True

    def get_queryset(self):
        po = self.get_parent_object()
        qs = get_user_queryset(self.request.user, UnifiedJob)
        qs = qs.filter(execution_node=po.hostname)
        return qs


class InstanceInstanceGroupsList(SubListAPIView):

    view_name = _("Instance's Instance Groups")
    model = InstanceGroup
    serializer_class = InstanceGroupSerializer
    parent_model = Instance
    new_in_320 = True
    relationship = 'rampart_groups'
