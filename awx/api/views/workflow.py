# Copyright (c) 2018 Ansible, Inc.
# All Rights Reserved.

# Python
from collections import OrderedDict
import six
import logging

# Django
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


# Django REST Framework
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.response import Response
from rest_framework import status

# AWX
from awx.main.utils import schedule_task_manager
from awx.api.versioning import get_request_version
from awx.api.views.credential import LaunchConfigCredentialsBase
from awx.api.views.jobtemplate import JobTemplateSurveySpec
from awx.main.models import (
    ActivityStream,
    Credential,
    WorkflowJobTemplate,
    NotificationTemplate,
    Role,
    User,
    WorkflowJob,
    WorkflowJobNode,
    WorkflowJobTemplateNode,
    Schedule,
    Notification,
)
from awx.api.generics import (
    RetrieveAPIView,
    GenericAPIView,
    SubListCreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    SubListAPIView,
    SubListCreateAttachDetachAPIView,
    ResourceAccessList,
    ListAPIView,
    CopyAPIView,
    RetrieveDestroyAPIView,
)
from awx.api.serializers import (
    ActivityStreamSerializer,
    RoleSerializer,
    NotificationTemplateSerializer,
    WorkflowJobTemplateSerializer,
    WorkflowJobNodeListSerializer,
    WorkflowJobNodeDetailSerializer,
    CredentialSerializer,
    WorkflowJobTemplateNodeSerializer,
    WorkflowJobTemplateNodeDetailSerializer,
    WorkflowJobLaunchSerializer,
    EmptySerializer,
    WorkflowJobSerializer,
    WorkflowJobListSerializer,
    ScheduleSerializer,
    WorkflowJobCancelSerializer,
    NotificationSerializer,
)
from awx.api.views.mixin import (
    ActivityStreamEnforcementMixin,
    WorkflowsEnforcementMixin,
    UnifiedJobDeletionMixin,
    RelatedJobsPreventDeleteMixin,
    EnforceParentRelationshipMixin,
)

logger = logging.getLogger('awx.api.views.workflow')


class WorkflowJobNodeList(WorkflowsEnforcementMixin, ListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)


class WorkflowJobNodeDetail(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeDetailSerializer


class WorkflowJobNodeCredentialsList(SubListAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    parent_model = WorkflowJobNode
    relationship = 'credentials'


class WorkflowJobTemplateNodeList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeSerializer
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)


class WorkflowJobTemplateNodeDetail(WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeDetailSerializer


class WorkflowJobTemplateNodeCredentialsList(LaunchConfigCredentialsBase):

    parent_model = WorkflowJobTemplateNode


class WorkflowJobTemplateNodeChildrenBaseList(WorkflowsEnforcementMixin, EnforceParentRelationshipMixin, SubListCreateAttachDetachAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeSerializer
    always_allow_superuser = True
    parent_model = WorkflowJobTemplateNode
    relationship = ''
    enforce_parent_relationship = 'workflow_job_template'
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)

    '''
    Limit the set of WorkflowJobTemplateNodes to the related nodes of specified by
    'relationship'
    '''
    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).all()

    def is_valid_relation(self, parent, sub, created=False):

        if created:
            return None

        workflow_nodes = parent.workflow_job_template.workflow_job_template_nodes.all().\
            prefetch_related('success_nodes', 'failure_nodes', 'always_nodes')
        graph = {}
        for workflow_node in workflow_nodes:
            graph[workflow_node.pk] = dict(node_object=workflow_node, metadata={'parent': None, 'traversed': False})

        find = False
        for node_type in ['success_nodes', 'failure_nodes', 'always_nodes']:
            for workflow_node in workflow_nodes:
                parent_node = graph[workflow_node.pk]
                related_nodes = getattr(parent_node['node_object'], node_type).all()
                for related_node in related_nodes:
                    sub_node = graph[related_node.pk]
                    sub_node['metadata']['parent'] = parent_node
                    if not find and parent == workflow_node and sub == related_node and self.relationship == node_type:
                        find = True
        if not find:
            sub_node = graph[sub.pk]
            parent_node = graph[parent.pk]
            if sub_node['metadata']['parent'] is not None:
                return {"Error": _("Multiple parent relationship not allowed.")}
            sub_node['metadata']['parent'] = parent_node
            iter_node = sub_node
            while iter_node is not None:
                if iter_node['metadata']['traversed']:
                    return {"Error": _("Cycle detected.")}
                iter_node['metadata']['traversed'] = True
                iter_node = iter_node['metadata']['parent']

        return None


class WorkflowJobTemplateNodeSuccessNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'success_nodes'


class WorkflowJobTemplateNodeFailureNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'failure_nodes'


class WorkflowJobTemplateNodeAlwaysNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'always_nodes'


class WorkflowJobNodeChildrenBaseList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    parent_model = WorkflowJobNode
    relationship = ''
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)

    #
    #Limit the set of WorkflowJobeNodes to the related nodes of specified by
    #'relationship'
    #
    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).all()


class WorkflowJobNodeSuccessNodesList(WorkflowJobNodeChildrenBaseList):
    relationship = 'success_nodes'


class WorkflowJobNodeFailureNodesList(WorkflowJobNodeChildrenBaseList):
    relationship = 'failure_nodes'


class WorkflowJobNodeAlwaysNodesList(WorkflowJobNodeChildrenBaseList):
    relationship = 'always_nodes'


class WorkflowJobTemplateList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJobTemplate
    serializer_class = WorkflowJobTemplateSerializer
    always_allow_superuser = False


class WorkflowJobTemplateDetail(RelatedJobsPreventDeleteMixin, WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = WorkflowJobTemplate
    serializer_class = WorkflowJobTemplateSerializer
    always_allow_superuser = False


class WorkflowJobTemplateCopy(WorkflowsEnforcementMixin, CopyAPIView):

    model = WorkflowJobTemplate
    copy_return_serializer_class = WorkflowJobTemplateSerializer

    def get(self, request, *args, **kwargs):
        if get_request_version(request) < 2:
            return self.v1_not_allowed()
        obj = self.get_object()
        if not request.user.can_access(obj.__class__, 'read', obj):
            raise PermissionDenied()
        can_copy, messages = request.user.can_access_with_errors(self.model, 'copy', obj)
        data = OrderedDict([
            ('can_copy', can_copy), ('can_copy_without_user_input', can_copy),
            ('templates_unable_to_copy', [] if can_copy else ['all']),
            ('credentials_unable_to_copy', [] if can_copy else ['all']),
            ('inventories_unable_to_copy', [] if can_copy else ['all'])
        ])
        if messages and can_copy:
            data['can_copy_without_user_input'] = False
            data.update(messages)
        return Response(data)

    @staticmethod
    def deep_copy_permission_check_func(user, new_objs):
        for obj in new_objs:
            for field_name in obj._get_workflow_job_field_names():
                item = getattr(obj, field_name, None)
                if item is None:
                    continue
                elif field_name in ['inventory']:
                    if not user.can_access(item.__class__, 'use', item):
                        setattr(obj, field_name, None)
                elif field_name in ['unified_job_template']:
                    if not user.can_access(item.__class__, 'start', item, validate_license=False):
                        setattr(obj, field_name, None)
                elif field_name in ['credentials']:
                    for cred in item.all():
                        if not user.can_access(cred.__class__, 'use', cred):
                            logger.debug(six.text_type(
                                'Deep copy: removing {} from relationship due to permissions').format(cred))
                            item.remove(cred.pk)
            obj.save()


class WorkflowJobTemplateLaunch(WorkflowsEnforcementMixin, RetrieveAPIView):


    model = WorkflowJobTemplate
    obj_permission_type = 'start'
    serializer_class = WorkflowJobLaunchSerializer
    always_allow_superuser = False

    def update_raw_data(self, data):
        try:
            obj = self.get_object()
        except PermissionDenied:
            return data
        extra_vars = data.pop('extra_vars', None) or {}
        if obj:
            for v in obj.variables_needed_to_start:
                extra_vars.setdefault(v, u'')
            if extra_vars:
                data['extra_vars'] = extra_vars
        return data

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        serializer = self.serializer_class(instance=obj, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        prompted_fields, ignored_fields, errors = obj._accept_or_ignore_job_kwargs(**request.data)

        new_job = obj.create_unified_job(**prompted_fields)
        new_job.signal_start()

        data = OrderedDict()
        data['workflow_job'] = new_job.id
        data['ignored_fields'] = ignored_fields
        data.update(WorkflowJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
        headers = {'Location': new_job.get_absolute_url(request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class WorkflowJobRelaunch(WorkflowsEnforcementMixin, GenericAPIView):

    model = WorkflowJob
    obj_permission_type = 'start'
    serializer_class = EmptySerializer

    def check_object_permissions(self, request, obj):
        if request.method == 'POST' and obj:
            relaunch_perm, messages = request.user.can_access_with_errors(self.model, 'start', obj)
            if not relaunch_perm and 'workflow_job_template' in messages:
                self.permission_denied(request, message=messages['workflow_job_template'])
        return super(WorkflowJobRelaunch, self).check_object_permissions(request, obj)

    def get(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.is_sliced_job and not obj.job_template_id:
            raise ParseError(_('Cannot relaunch slice workflow job orphaned from job template.'))
        new_workflow_job = obj.create_relaunch_workflow_job()
        new_workflow_job.signal_start()

        data = WorkflowJobSerializer(new_workflow_job, context=self.get_serializer_context()).data
        headers = {'Location': new_workflow_job.get_absolute_url(request=request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class WorkflowJobTemplateWorkflowNodesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'workflow_job_template_nodes'
    parent_key = 'workflow_job_template'
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)

    def get_queryset(self):
        return super(WorkflowJobTemplateWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobTemplateJobsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobListSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'workflow_jobs'
    parent_key = 'workflow_job_template'


class WorkflowJobTemplateSchedulesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    view_name = _("Workflow Job Template Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class WorkflowJobTemplateNotificationTemplatesAnyList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_any'


class WorkflowJobTemplateNotificationTemplatesErrorList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_error'


class WorkflowJobTemplateNotificationTemplatesSuccessList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_success'


class WorkflowJobTemplateAccessList(WorkflowsEnforcementMixin, ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = WorkflowJobTemplate


class WorkflowJobTemplateObjectRolesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = WorkflowJobTemplate
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class WorkflowJobTemplateActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(workflow_job_template=parent) |
                         Q(workflow_job_template_node__workflow_job_template=parent)).distinct()


class WorkflowJobList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobListSerializer


class WorkflowJobDetail(WorkflowsEnforcementMixin, UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobSerializer


class WorkflowJobWorkflowNodesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    always_allow_superuser = True
    parent_model = WorkflowJob
    relationship = 'workflow_job_nodes'
    parent_key = 'workflow_job'
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)

    def get_queryset(self):
        return super(WorkflowJobWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobCancel(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = WorkflowJob
    obj_permission_type = 'cancel'
    serializer_class = WorkflowJobCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            schedule_task_manager()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class WorkflowJobNotificationsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = WorkflowJob
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class WorkflowJobActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = WorkflowJob
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class WorkflowJobTemplateSurveySpec(WorkflowsEnforcementMixin, JobTemplateSurveySpec):
    model = WorkflowJobTemplate
