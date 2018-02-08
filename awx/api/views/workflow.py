# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging
from collections import OrderedDict

# Django
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q


# Django REST Framework
from rest_framework.response import Response
from rest_framework import status

# AWX
from awx.api.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveDestroyAPIView,
    SubListAPIView,
    SubListCreateAPIView,
    SubListCreateAttachDetachAPIView,
    GenericAPIView,
)
from awx.api.views import (
    JobLabelList,
    JobTemplateLabelList,
    ResourceAccessList,
)
from awx.api.views.mixins import (
    ActivityStreamEnforcementMixin,
    WorkflowsEnforcementMixin,
    EnforceParentRelationshipMixin,
    UnifiedJobDeletionMixin,
)
from awx.main.models import (
    ActivityStream,
    JobTemplateSurveySpec,
    Notification,
    NotificationTemplate,
    WorkflowJobNode,
    WorkflowJobTemplateNode,
    WorkflowJobTemplate,
    WorkflowJob,
    Schedule,
    User,
    Role,
)

from awx.api.permissions import (
    PermissionDenied,
)
from awx.api.serializers import (
    ActivityStreamSerializer,
    NotificationSerializer,
    NotificationTemplateSerializer,
    WorkflowJobSerializer,
    WorkflowJobNodeListSerializer,
    WorkflowJobNodeDetailSerializer,
    WorkflowJobTemplateSerializer,
    WorkflowJobTemplateListSerializer,
    WorkflowJobTemplateNodeListSerializer,
    WorkflowJobTemplateNodeDetailSerializer,
    WorkflowJobLaunchSerializer,
    WorkflowJobListSerializer,
    WorkflowJobCancelSerializer,
    ScheduleSerializer,
    RoleSerializer,
    EmptySerializer,
)
from awx.main.scheduler.tasks import run_job_complete

logger = logging.getLogger('awx.api.views')



class WorkflowJobTemplateSurveySpec(WorkflowsEnforcementMixin, JobTemplateSurveySpec):

    model = WorkflowJobTemplate
    new_in_310 = True


class WorkflowJobNodeList(WorkflowsEnforcementMixin, ListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    new_in_310 = True


class WorkflowJobNodeDetail(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeDetailSerializer
    new_in_310 = True


class WorkflowJobTemplateNodeList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeListSerializer
    new_in_310 = True


class WorkflowJobTemplateNodeDetail(WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeDetailSerializer
    new_in_310 = True

    def update_raw_data(self, data):
        for fd in ['job_type', 'job_tags', 'skip_tags', 'limit', 'skip_tags']:
            data[fd] = None
        try:
            obj = self.get_object()
            data.update(obj.char_prompts)
        except Exception:
            pass
        return super(WorkflowJobTemplateNodeDetail, self).update_raw_data(data)


class WorkflowJobTemplateNodeChildrenBaseList(WorkflowsEnforcementMixin, EnforceParentRelationshipMixin, SubListCreateAttachDetachAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeListSerializer
    always_allow_superuser = True
    parent_model = WorkflowJobTemplateNode
    relationship = ''
    enforce_parent_relationship = 'workflow_job_template'
    new_in_310 = True

    '''
    Limit the set of WorkflowJobTemplateNodes to the related nodes of specified by
    'relationship'
    '''
    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).all()

    def is_valid_relation(self, parent, sub, created=False):
        mutex_list = ('success_nodes', 'failure_nodes') if self.relationship == 'always_nodes' else ('always_nodes',)
        for relation in mutex_list:
            if getattr(parent, relation).all().exists():
                return {'Error': _('Cannot associate {0} when {1} have been associated.').format(self.relationship, relation)}

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
    new_in_310 = True

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
    serializer_class = WorkflowJobTemplateListSerializer
    always_allow_superuser = False
    new_in_310 = True


class WorkflowJobTemplateDetail(WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = WorkflowJobTemplate
    serializer_class = WorkflowJobTemplateSerializer
    always_allow_superuser = False
    new_in_310 = True


class WorkflowJobTemplateCopy(WorkflowsEnforcementMixin, GenericAPIView):

    model = WorkflowJobTemplate
    serializer_class = EmptySerializer
    new_in_310 = True

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
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

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'copy', obj):
            raise PermissionDenied()
        new_obj = obj.user_copy(request.user)
        if request.user not in new_obj.admin_role:
            new_obj.admin_role.members.add(request.user)
        data = OrderedDict()
        data.update(WorkflowJobTemplateSerializer(
            new_obj, context=self.get_serializer_context()).to_representation(new_obj))
        return Response(data, status=status.HTTP_201_CREATED)


class WorkflowJobTemplateLabelList(WorkflowsEnforcementMixin, JobTemplateLabelList):
    parent_model = WorkflowJobTemplate
    new_in_310 = True


class WorkflowJobTemplateLaunch(WorkflowsEnforcementMixin, RetrieveAPIView):


    model = WorkflowJobTemplate
    obj_permission_type = 'start'
    serializer_class = WorkflowJobLaunchSerializer
    new_in_310 = True
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

        prompted_fields, ignored_fields = obj._accept_or_ignore_job_kwargs(**request.data)

        new_job = obj.create_unified_job(**prompted_fields)
        new_job.signal_start()

        data = OrderedDict()
        data['workflow_job'] = new_job.id
        data['ignored_fields'] = ignored_fields
        data.update(WorkflowJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
        return Response(data, status=status.HTTP_201_CREATED)


class WorkflowJobRelaunch(WorkflowsEnforcementMixin, GenericAPIView):

    model = WorkflowJob
    obj_permission_type = 'start'
    serializer_class = EmptySerializer
    new_in_310 = True

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
        new_workflow_job = obj.create_relaunch_workflow_job()
        new_workflow_job.signal_start()

        data = WorkflowJobSerializer(new_workflow_job, context=self.get_serializer_context()).data
        headers = {'Location': new_workflow_job.get_absolute_url(request=request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class WorkflowJobTemplateWorkflowNodesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeListSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'workflow_job_template_nodes'
    parent_key = 'workflow_job_template'
    new_in_310 = True

    def update_raw_data(self, data):
        for fd in ['job_type', 'job_tags', 'skip_tags', 'limit', 'skip_tags']:
            data[fd] = None
        return super(WorkflowJobTemplateWorkflowNodesList, self).update_raw_data(data)

    def get_queryset(self):
        return super(WorkflowJobTemplateWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobTemplateJobsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobListSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'workflow_jobs'
    parent_key = 'workflow_job_template'
    new_in_310 = True


class WorkflowJobTemplateSchedulesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    view_name = _("Workflow Job Template Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_310 = True


class WorkflowJobTemplateNotificationTemplatesAnyList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_any'
    new_in_310 = True


class WorkflowJobTemplateNotificationTemplatesErrorList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_error'
    new_in_310 = True


class WorkflowJobTemplateNotificationTemplatesSuccessList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_success'
    new_in_310 = True


class WorkflowJobTemplateAccessList(WorkflowsEnforcementMixin, ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = WorkflowJobTemplate
    new_in_310 = True


class WorkflowJobTemplateObjectRolesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = WorkflowJobTemplate
    new_in_310 = True

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class WorkflowJobTemplateActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'activitystream_set'
    new_in_310 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(workflow_job_template=parent) |
                         Q(workflow_job_template_node__workflow_job_template=parent)).distinct()


class WorkflowJobList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobListSerializer
    new_in_310 = True


class WorkflowJobDetail(WorkflowsEnforcementMixin, UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobSerializer
    new_in_310 = True


class WorkflowJobWorkflowNodesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    always_allow_superuser = True
    parent_model = WorkflowJob
    relationship = 'workflow_job_nodes'
    parent_key = 'workflow_job'
    new_in_310 = True

    def get_queryset(self):
        return super(WorkflowJobWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobCancel(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = WorkflowJob
    obj_permission_type = 'cancel'
    serializer_class = WorkflowJobCancelSerializer
    new_in_310 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            #TODO: Figure out whether an immediate schedule is needed.
            run_job_complete.delay(obj.id)
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class WorkflowJobNotificationsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = WorkflowJob
    relationship = 'notifications'
    new_in_310 = True


class WorkflowJobActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = WorkflowJob
    relationship = 'activitystream_set'
    new_in_310 = True


class WorkflowJobLabelList(WorkflowsEnforcementMixin, JobLabelList):
    parent_model = WorkflowJob
    new_in_310 = True
