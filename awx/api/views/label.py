# Copyright (c) 2018 Ansible, Inc.
# All Rights Reserved.

# Django
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.response import Response
from rest_framework import status

# AWX
from awx.api.serializers import LabelSerializer
from awx.api.views.mixin import WorkflowsEnforcementMixin
from awx.api.generics import (
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    SubListAPIView,
    SubListCreateAttachDetachAPIView,
    DeleteLastUnattachLabelMixin,
)
from awx.main.models import (
    Label,
    Job,
    JobTemplate,
    WorkflowJob,
    WorkflowJobTemplate,
)


class LabelList(ListCreateAPIView):

    model = Label
    serializer_class = LabelSerializer


class LabelDetail(RetrieveUpdateAPIView):

    model = Label
    serializer_class = LabelSerializer


class JobLabelList(SubListAPIView):

    model = Label
    serializer_class = LabelSerializer
    parent_model = Job
    relationship = 'labels'
    parent_key = 'job'


class JobTemplateLabelList(DeleteLastUnattachLabelMixin, SubListCreateAttachDetachAPIView):

    model = Label
    serializer_class = LabelSerializer
    parent_model = JobTemplate
    relationship = 'labels'

    def post(self, request, *args, **kwargs):
        # If a label already exists in the database, attach it instead of erroring out
        # that it already exists
        if 'id' not in request.data and 'name' in request.data and 'organization' in request.data:
            existing = Label.objects.filter(name=request.data['name'], organization_id=request.data['organization'])
            if existing.exists():
                existing = existing[0]
                request.data['id'] = existing.id
                del request.data['name']
                del request.data['organization']
        if Label.objects.filter(unifiedjobtemplate_labels=self.kwargs['pk']).count() > 100:
            return Response(dict(msg=_('Maximum number of labels for {} reached.'.format(
                self.parent_model._meta.verbose_name_raw))), status=status.HTTP_400_BAD_REQUEST)
        return super(JobTemplateLabelList, self).post(request, *args, **kwargs)


class WorkflowJobTemplateLabelList(WorkflowsEnforcementMixin, JobTemplateLabelList):
    parent_model = WorkflowJobTemplate


class WorkflowJobLabelList(WorkflowsEnforcementMixin, JobLabelList):
    parent_model = WorkflowJob
