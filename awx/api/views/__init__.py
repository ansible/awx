# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import re
import cgi
import dateutil
import time
import sys
import requests
from base64 import b64encode
from collections import OrderedDict
import six


# Django
from django.conf import settings
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.db.models import Q
from django.db import IntegrityError, transaction, connection
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


# Django REST Framework
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler
from rest_framework import status

# Django REST Framework YAML
from rest_framework_yaml.parsers import YAMLParser
from rest_framework_yaml.renderers import YAMLRenderer

# QSStats
import qsstats

# ANSIConv
import ansiconv

# Python Social Auth
from social_core.backends.utils import load_backends

# Django OAuth Toolkit
from oauth2_provider.models import get_access_token_model

import pytz
from wsgiref.util import FileWrapper

# AWX
from awx.main.tasks import send_notifications
from awx.main.access import get_user_queryset
from awx.api.filters import V1CredentialFilterBackend
from awx.api.generics import get_view_name
from awx.api.generics import * # noqa
from awx.api.versioning import reverse, get_request_version
from awx.conf.license import feature_enabled, feature_exists
from awx.main.models import * # noqa
from awx.main.utils import * # noqa
from awx.main.utils import decrypt_field
from awx.main.utils.filters import SmartFilter
from awx.main.utils.insights import filter_insights_api_response
from awx.main.redact import UriCleaner
from awx.api.permissions import (
    TaskPermission,
    ProjectUpdatePermission,
    InventoryInventorySourcesUpdatePermission,
    UserPermission,
    InstanceGroupTowerPermission,
)
from awx.api.renderers import * # noqa
from awx.api.serializers import * # noqa
from awx.api.metadata import RoleMetadata, JobTypeMetadata
from awx.main.constants import ACTIVE_STATES
from awx.api.views.credential import LaunchConfigCredentialsBase
from awx.api.views.mixin import (
    ActivityStreamEnforcementMixin,
    SystemTrackingEnforcementMixin,
    UnifiedJobDeletionMixin,
    InstanceGroupMembershipMixin,
    RelatedJobsPreventDeleteMixin,
    OrganizationCountsMixin,
    ControlledByScmMixin,
    EnforceParentRelationshipMixin,
)
from awx.api.views.organization import ( # noqa
    OrganizationList,
    OrganizationDetail,
    OrganizationInventoriesList,
    OrganizationUsersList,
    OrganizationAdminsList,
    OrganizationProjectsList,
    OrganizationWorkflowJobTemplatesList,
    OrganizationTeamsList,
    OrganizationActivityStreamList,
    OrganizationNotificationTemplatesList,
    OrganizationNotificationTemplatesAnyList,
    OrganizationNotificationTemplatesErrorList,
    OrganizationNotificationTemplatesSuccessList,
    OrganizationInstanceGroupsList,
    OrganizationAccessList,
    OrganizationObjectRolesList,
)
from awx.api.views.inventory import ( # noqa
    InventoryList,
    InventoryDetail,
    InventoryUpdateEventsList,
    InventoryScriptList,
    InventoryScriptDetail,
    InventoryScriptObjectRolesList,
    InventoryScriptCopy,
    InventoryList,
    InventoryDetail,
    InventoryActivityStreamList,
    InventoryInstanceGroupsList,
    InventoryAccessList,
    InventoryObjectRolesList,
    InventoryJobTemplateList,
    InventoryCopy,
)
from awx.api.views.workflow import ( # noqa
    WorkflowJobNodeList,
    WorkflowJobNodeDetail,
    WorkflowJobNodeCredentialsList,
    WorkflowJobTemplateNodeList,
    WorkflowJobTemplateNodeDetail,
    WorkflowJobTemplateNodeCredentialsList,
    WorkflowJobTemplateNodeChildrenBaseList,
    WorkflowJobTemplateNodeSuccessNodesList,
    WorkflowJobTemplateNodeFailureNodesList,
    WorkflowJobTemplateNodeAlwaysNodesList,
    WorkflowJobNodeChildrenBaseList,
    WorkflowJobNodeSuccessNodesList,
    WorkflowJobNodeFailureNodesList,
    WorkflowJobNodeAlwaysNodesList,
    WorkflowJobTemplateList,
    WorkflowJobTemplateDetail,
    WorkflowJobTemplateCopy,
    WorkflowJobTemplateLaunch,
    WorkflowJobRelaunch,
    WorkflowJobTemplateWorkflowNodesList,
    WorkflowJobTemplateJobsList,
    WorkflowJobTemplateSchedulesList,
    WorkflowJobTemplateNotificationTemplatesAnyList,
    WorkflowJobTemplateNotificationTemplatesErrorList,
    WorkflowJobTemplateNotificationTemplatesSuccessList,
    WorkflowJobTemplateAccessList,
    WorkflowJobTemplateObjectRolesList,
    WorkflowJobTemplateActivityStreamList,
    WorkflowJobList,
    WorkflowJobDetail,
    WorkflowJobWorkflowNodesList,
    WorkflowJobCancel,
    WorkflowJobNotificationsList,
    WorkflowJobActivityStreamList,
    WorkflowJobTemplateSurveySpec,
)
from awx.api.views.jobtemplate import ( # noqa
    JobTemplateList,
    JobTemplateDetail,
    JobTemplateLaunch,
    JobTemplateSchedulesList,
    JobTemplateSurveySpec,
    JobTemplateActivityStreamList,
    JobTemplateNotificationTemplatesAnyList,
    JobTemplateNotificationTemplatesErrorList,
    JobTemplateNotificationTemplatesSuccessList,
    JobTemplateCredentialsList,
    JobTemplateExtraCredentialsList,
    JobTemplateCallback,
    JobTemplateJobsList,
    JobTemplateSliceWorkflowJobsList,
    JobTemplateInstanceGroupsList,
    JobTemplateAccessList,
    JobTemplateObjectRolesList,
    JobTemplateCopy,
)
from awx.api.views.label import ( # noqa
    LabelList,
    LabelDetail,
    JobLabelList,
    JobTemplateLabelList,
    WorkflowJobLabelList,
    WorkflowJobTemplateLabelList,
)
from awx.api.views.root import ( # noqa
    ApiRootView,
    ApiOAuthAuthorizationRootView,
    ApiVersionRootView,
    ApiV1RootView,
    ApiV2RootView,
    ApiV1PingView,
    ApiV1ConfigView,
)


def api_exception_handler(exc, context):
    '''
    Override default API exception handler to catch IntegrityError exceptions.
    '''
    if isinstance(exc, IntegrityError):
        exc = ParseError(exc.args[0])
    if isinstance(exc, FieldError):
        exc = ParseError(exc.args[0])
    if isinstance(context['view'], UnifiedJobStdout):
        context['view'].renderer_classes = [BrowsableAPIRenderer, renderers.JSONRenderer]
    return exception_handler(exc, context)


class DashboardView(APIView):

    view_name = _("Dashboard")
    swagger_topic = 'Dashboard'

    def get(self, request, format=None):
        ''' Show Dashboard Details '''
        data = OrderedDict()
        data['related'] = {'jobs_graph': reverse('api:dashboard_jobs_graph_view', request=request)}
        user_inventory = get_user_queryset(request.user, Inventory)
        inventory_with_failed_hosts = user_inventory.filter(hosts_with_active_failures__gt=0)
        user_inventory_external = user_inventory.filter(has_inventory_sources=True)
        failed_inventory = sum(i.inventory_sources_with_failures for i in user_inventory)
        data['inventories'] = {'url': reverse('api:inventory_list', request=request),
                               'total': user_inventory.count(),
                               'total_with_inventory_source': user_inventory_external.count(),
                               'job_failed': inventory_with_failed_hosts.count(),
                               'inventory_failed': failed_inventory}
        user_inventory_sources = get_user_queryset(request.user, InventorySource)
        ec2_inventory_sources = user_inventory_sources.filter(source='ec2')
        ec2_inventory_failed = ec2_inventory_sources.filter(status='failed')
        data['inventory_sources'] = {}
        data['inventory_sources']['ec2'] = {'url': reverse('api:inventory_source_list', request=request) + "?source=ec2",
                                            'failures_url': reverse('api:inventory_source_list', request=request) + "?source=ec2&status=failed",
                                            'label': 'Amazon EC2',
                                            'total': ec2_inventory_sources.count(),
                                            'failed': ec2_inventory_failed.count()}

        user_groups = get_user_queryset(request.user, Group)
        groups_job_failed = (Group.objects.filter(hosts_with_active_failures__gt=0) | Group.objects.filter(groups_with_active_failures__gt=0)).count()
        groups_inventory_failed = Group.objects.filter(inventory_sources__last_job_failed=True).count()
        data['groups'] = {'url': reverse('api:group_list', request=request),
                          'failures_url': reverse('api:group_list', request=request) + "?has_active_failures=True",
                          'total': user_groups.count(),
                          'job_failed': groups_job_failed,
                          'inventory_failed': groups_inventory_failed}

        user_hosts = get_user_queryset(request.user, Host)
        user_hosts_failed = user_hosts.filter(has_active_failures=True)
        data['hosts'] = {'url': reverse('api:host_list', request=request),
                         'failures_url': reverse('api:host_list', request=request) + "?has_active_failures=True",
                         'total': user_hosts.count(),
                         'failed': user_hosts_failed.count()}

        user_projects = get_user_queryset(request.user, Project)
        user_projects_failed = user_projects.filter(last_job_failed=True)
        data['projects'] = {'url': reverse('api:project_list', request=request),
                            'failures_url': reverse('api:project_list', request=request) + "?last_job_failed=True",
                            'total': user_projects.count(),
                            'failed': user_projects_failed.count()}

        git_projects = user_projects.filter(scm_type='git')
        git_failed_projects = git_projects.filter(last_job_failed=True)
        svn_projects = user_projects.filter(scm_type='svn')
        svn_failed_projects = svn_projects.filter(last_job_failed=True)
        hg_projects = user_projects.filter(scm_type='hg')
        hg_failed_projects = hg_projects.filter(last_job_failed=True)
        data['scm_types'] = {}
        data['scm_types']['git'] = {'url': reverse('api:project_list', request=request) + "?scm_type=git",
                                    'label': 'Git',
                                    'failures_url': reverse('api:project_list', request=request) + "?scm_type=git&last_job_failed=True",
                                    'total': git_projects.count(),
                                    'failed': git_failed_projects.count()}
        data['scm_types']['svn'] = {'url': reverse('api:project_list', request=request) + "?scm_type=svn",
                                    'label': 'Subversion',
                                    'failures_url': reverse('api:project_list', request=request) + "?scm_type=svn&last_job_failed=True",
                                    'total': svn_projects.count(),
                                    'failed': svn_failed_projects.count()}
        data['scm_types']['hg'] = {'url': reverse('api:project_list', request=request) + "?scm_type=hg",
                                   'label': 'Mercurial',
                                   'failures_url': reverse('api:project_list', request=request) + "?scm_type=hg&last_job_failed=True",
                                   'total': hg_projects.count(),
                                   'failed': hg_failed_projects.count()}

        user_jobs = get_user_queryset(request.user, Job)
        user_failed_jobs = user_jobs.filter(failed=True)
        data['jobs'] = {'url': reverse('api:job_list', request=request),
                        'failure_url': reverse('api:job_list', request=request) + "?failed=True",
                        'total': user_jobs.count(),
                        'failed': user_failed_jobs.count()}

        user_list = get_user_queryset(request.user, User)
        team_list = get_user_queryset(request.user, Team)
        credential_list = get_user_queryset(request.user, Credential)
        job_template_list = get_user_queryset(request.user, JobTemplate)
        organization_list = get_user_queryset(request.user, Organization)
        data['users'] = {'url': reverse('api:user_list', request=request),
                         'total': user_list.count()}
        data['organizations'] = {'url': reverse('api:organization_list', request=request),
                                 'total': organization_list.count()}
        data['teams'] = {'url': reverse('api:team_list', request=request),
                         'total': team_list.count()}
        data['credentials'] = {'url': reverse('api:credential_list', request=request),
                               'total': credential_list.count()}
        data['job_templates'] = {'url': reverse('api:job_template_list', request=request),
                                 'total': job_template_list.count()}
        return Response(data)


class DashboardJobsGraphView(APIView):

    view_name = _("Dashboard Jobs Graphs")
    swagger_topic = 'Jobs'

    def get(self, request, format=None):
        period = request.query_params.get('period', 'month')
        job_type = request.query_params.get('job_type', 'all')

        user_unified_jobs = get_user_queryset(request.user, UnifiedJob)

        success_query = user_unified_jobs.filter(status='successful')
        failed_query = user_unified_jobs.filter(status='failed')

        if job_type == 'inv_sync':
            success_query = success_query.filter(instance_of=InventoryUpdate)
            failed_query = failed_query.filter(instance_of=InventoryUpdate)
        elif job_type == 'playbook_run':
            success_query = success_query.filter(instance_of=Job)
            failed_query = failed_query.filter(instance_of=Job)
        elif job_type == 'scm_update':
            success_query = success_query.filter(instance_of=ProjectUpdate)
            failed_query = failed_query.filter(instance_of=ProjectUpdate)

        success_qss = qsstats.QuerySetStats(success_query, 'finished')
        failed_qss = qsstats.QuerySetStats(failed_query, 'finished')

        start_date = now()
        if period == 'month':
            end_date = start_date - dateutil.relativedelta.relativedelta(months=1)
            interval = 'days'
        elif period == 'week':
            end_date = start_date - dateutil.relativedelta.relativedelta(weeks=1)
            interval = 'days'
        elif period == 'day':
            end_date = start_date - dateutil.relativedelta.relativedelta(days=1)
            interval = 'hours'
        else:
            return Response({'error': _('Unknown period "%s"') % str(period)}, status=status.HTTP_400_BAD_REQUEST)

        dashboard_data = {"jobs": {"successful": [], "failed": []}}
        for element in success_qss.time_series(end_date, start_date, interval=interval):
            dashboard_data['jobs']['successful'].append([time.mktime(element[0].timetuple()),
                                                         element[1]])
        for element in failed_qss.time_series(end_date, start_date, interval=interval):
            dashboard_data['jobs']['failed'].append([time.mktime(element[0].timetuple()),
                                                     element[1]])
        return Response(dashboard_data)


class InstanceList(ListAPIView):

    view_name = _("Instances")
    model = Instance
    serializer_class = InstanceSerializer
    search_fields = ('hostname',)


class InstanceDetail(RetrieveUpdateAPIView):

    view_name = _("Instance Detail")
    model = Instance
    serializer_class = InstanceSerializer


    def update(self, request, *args, **kwargs):
        r = super(InstanceDetail, self).update(request, *args, **kwargs)
        if status.is_success(r.status_code):
            obj = self.get_object()
            if obj.enabled:
                obj.refresh_capacity()
            else:
                obj.capacity = 0
            obj.save()
            r.data = InstanceSerializer(obj, context=self.get_serializer_context()).to_representation(obj)
        return r


class InstanceUnifiedJobsList(SubListAPIView):

    view_name = _("Instance Jobs")
    model = UnifiedJob
    serializer_class = UnifiedJobListSerializer
    parent_model = Instance

    def get_queryset(self):
        po = self.get_parent_object()
        qs = get_user_queryset(self.request.user, UnifiedJob)
        qs = qs.filter(execution_node=po.hostname)
        return qs


class InstanceInstanceGroupsList(InstanceGroupMembershipMixin, SubListCreateAttachDetachAPIView):

    view_name = _("Instance's Instance Groups")
    model = InstanceGroup
    serializer_class = InstanceGroupSerializer
    parent_model = Instance
    relationship = 'rampart_groups'


class InstanceGroupList(ListCreateAPIView):

    view_name = _("Instance Groups")
    model = InstanceGroup
    serializer_class = InstanceGroupSerializer


class InstanceGroupDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):

    always_allow_superuser = False
    view_name = _("Instance Group Detail")
    model = InstanceGroup
    serializer_class = InstanceGroupSerializer
    permission_classes = (InstanceGroupTowerPermission,)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.controller is not None:
            raise PermissionDenied(detail=_("Isolated Groups can not be removed from the API"))
        if instance.controlled_groups.count():
            raise PermissionDenied(detail=_("Instance Groups acting as a controller for an Isolated Group can not be removed from the API"))
        return super(InstanceGroupDetail, self).destroy(request, *args, **kwargs)


class InstanceGroupUnifiedJobsList(SubListAPIView):

    view_name = _("Instance Group Running Jobs")
    model = UnifiedJob
    serializer_class = UnifiedJobListSerializer
    parent_model = InstanceGroup
    relationship = "unifiedjob_set"


class InstanceGroupInstanceList(InstanceGroupMembershipMixin, SubListAttachDetachAPIView):

    view_name = _("Instance Group's Instances")
    model = Instance
    serializer_class = InstanceSerializer
    parent_model = InstanceGroup
    relationship = "instances"
    search_fields = ('hostname',)


class ScheduleList(ListCreateAPIView):

    view_name = _("Schedules")
    model = Schedule
    serializer_class = ScheduleSerializer


class ScheduleDetail(RetrieveUpdateDestroyAPIView):

    model = Schedule
    serializer_class = ScheduleSerializer


class SchedulePreview(GenericAPIView):

    model = Schedule
    view_name = _('Schedule Recurrence Rule Preview')
    serializer_class = SchedulePreviewSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            next_stamp = now()
            schedule = []
            gen = Schedule.rrulestr(serializer.validated_data['rrule']).xafter(next_stamp, count=20)

            # loop across the entire generator and grab the first 10 events
            for event in gen:
                if len(schedule) >= 10:
                    break
                if not dateutil.tz.datetime_exists(event):
                    # skip imaginary dates, like 2:30 on DST boundaries
                    continue
                schedule.append(event)

            return Response({
                'local': schedule,
                'utc': [s.astimezone(pytz.utc) for s in schedule]
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleZoneInfo(APIView):

    swagger_topic = 'System Configuration'

    def get(self, request):
        zones = [
            {'name': zone}
            for zone in Schedule.get_zoneinfo()
        ]
        return Response(zones)


class ScheduleCredentialsList(LaunchConfigCredentialsBase):

    parent_model = Schedule


class ScheduleUnifiedJobsList(SubListAPIView):

    model = UnifiedJob
    serializer_class = UnifiedJobListSerializer
    parent_model = Schedule
    relationship = 'unifiedjob_set'
    view_name = _('Schedule Jobs List')


class AuthView(APIView):
    ''' List enabled single-sign-on endpoints '''

    authentication_classes = []
    permission_classes = (AllowAny,)
    swagger_topic = 'System Configuration'

    def get(self, request):
        from rest_framework.reverse import reverse
        data = OrderedDict()
        err_backend, err_message = request.session.get('social_auth_error', (None, None))
        auth_backends = load_backends(settings.AUTHENTICATION_BACKENDS, force_load=True).items()
        # Return auth backends in consistent order: Google, GitHub, SAML.
        auth_backends.sort(key=lambda x: 'g' if x[0] == 'google-oauth2' else x[0])
        for name, backend in auth_backends:
            if (not feature_exists('enterprise_auth') and
                not feature_enabled('ldap')) or \
                (not feature_enabled('enterprise_auth') and
                 name in ['saml', 'radius']):
                    continue

            login_url = reverse('social:begin', args=(name,))
            complete_url = request.build_absolute_uri(reverse('social:complete', args=(name,)))
            backend_data = {
                'login_url': login_url,
                'complete_url': complete_url,
            }
            if name == 'saml':
                backend_data['metadata_url'] = reverse('sso:saml_metadata')
                for idp in sorted(settings.SOCIAL_AUTH_SAML_ENABLED_IDPS.keys()):
                    saml_backend_data = dict(backend_data.items())
                    saml_backend_data['login_url'] = '%s?idp=%s' % (login_url, idp)
                    full_backend_name = '%s:%s' % (name, idp)
                    if (err_backend == full_backend_name or err_backend == name) and err_message:
                        saml_backend_data['error'] = err_message
                    data[full_backend_name] = saml_backend_data
            else:
                if err_backend == name and err_message:
                    backend_data['error'] = err_message
                data[name] = backend_data
        return Response(data)


class TeamList(ListCreateAPIView):

    model = Team
    serializer_class = TeamSerializer


class TeamDetail(RetrieveUpdateDestroyAPIView):

    model = Team
    serializer_class = TeamSerializer


class TeamUsersList(BaseUsersList):

    model = User
    serializer_class = UserSerializer
    parent_model = Team
    relationship = 'member_role.members'


class TeamRolesList(SubListAttachDetachAPIView):

    model = Role
    serializer_class = RoleSerializerWithParentAccess
    metadata_class = RoleMetadata
    parent_model = Team
    relationship='member_role.children'
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        if not self.request.user.can_access(Team, 'read', team):
            raise PermissionDenied()
        return Role.filter_visible_roles(self.request.user, team.member_role.children.all().exclude(pk=team.read_role.pk))

    def post(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if not sub_id:
            return super(TeamRolesList, self).post(request)

        role = get_object_or_400(Role, pk=sub_id)
        org_content_type = ContentType.objects.get_for_model(Organization)
        if role.content_type == org_content_type and role.role_field in ['member_role', 'admin_role']:
            data = dict(msg=_("You cannot assign an Organization participation role as a child role for a Team."))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if role.is_singleton():
            data = dict(msg=_("You cannot grant system-level permissions to a team."))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        team = get_object_or_404(Team, pk=self.kwargs['pk'])
        credential_content_type = ContentType.objects.get_for_model(Credential)
        if role.content_type == credential_content_type:
            if not role.content_object.organization or role.content_object.organization.id != team.organization.id:
                data = dict(msg=_("You cannot grant credential access to a team when the Organization field isn't set, or belongs to a different organization"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        return super(TeamRolesList, self).post(request, *args, **kwargs)


class TeamObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Team
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class TeamProjectsList(SubListAPIView):

    model = Project
    serializer_class = ProjectSerializer
    parent_model = Team

    def get_queryset(self):
        team = self.get_parent_object()
        self.check_parent_access(team)
        model_ct = ContentType.objects.get_for_model(self.model)
        parent_ct = ContentType.objects.get_for_model(self.parent_model)
        proj_roles = Role.objects.filter(
            Q(ancestors__content_type=parent_ct) & Q(ancestors__object_id=team.pk),
            content_type=model_ct
        )
        return self.model.accessible_objects(self.request.user, 'read_role').filter(pk__in=[t.content_object.pk for t in proj_roles])


class TeamActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Team
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)

        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(team=parent) |
                         Q(project__in=Project.accessible_objects(parent, 'read_role')) |
                         Q(credential__in=Credential.accessible_objects(parent, 'read_role')))


class TeamAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = Team


class ProjectList(ListCreateAPIView):

    model = Project
    serializer_class = ProjectSerializer

    def get_queryset(self):
        projects_qs = Project.accessible_objects(self.request.user, 'read_role')
        projects_qs = projects_qs.select_related(
            'organization',
            'admin_role',
            'use_role',
            'update_role',
            'read_role',
        )
        projects_qs = projects_qs.prefetch_related('last_job', 'created_by')
        return projects_qs


class ProjectDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):

    model = Project
    serializer_class = ProjectSerializer


class ProjectPlaybooks(RetrieveAPIView):

    model = Project
    serializer_class = ProjectPlaybooksSerializer


class ProjectInventories(RetrieveAPIView):

    model = Project
    serializer_class = ProjectInventoriesSerializer


class ProjectTeamsList(ListAPIView):

    model = Team
    serializer_class = TeamSerializer

    def get_queryset(self):
        p = get_object_or_404(Project, pk=self.kwargs['pk'])
        if not self.request.user.can_access(Project, 'read', p):
            raise PermissionDenied()
        project_ct = ContentType.objects.get_for_model(Project)
        team_ct = ContentType.objects.get_for_model(self.model)
        all_roles = Role.objects.filter(Q(descendents__content_type=project_ct) & Q(descendents__object_id=p.pk), content_type=team_ct)
        return self.model.accessible_objects(self.request.user, 'read_role').filter(pk__in=[t.content_object.pk for t in all_roles])


class ProjectSchedulesList(SubListCreateAPIView):

    view_name = _("Project Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = Project
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class ProjectScmInventorySources(SubListAPIView):

    view_name = _("Project SCM Inventory Sources")
    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Project
    relationship = 'scm_inventory_sources'
    parent_key = 'source_project'


class ProjectActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Project
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        if parent is None:
            return qs
        elif parent.credential is None:
            return qs.filter(project=parent)
        return qs.filter(Q(project=parent) | Q(credential=parent.credential))


class ProjectNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = Project
    relationship = 'notification_templates_any'


class ProjectNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = Project
    relationship = 'notification_templates_error'


class ProjectNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = Project
    relationship = 'notification_templates_success'


class ProjectUpdatesList(SubListAPIView):

    model = ProjectUpdate
    serializer_class = ProjectUpdateListSerializer
    parent_model = Project
    relationship = 'project_updates'


class ProjectUpdateView(RetrieveAPIView):

    model = Project
    serializer_class = ProjectUpdateViewSerializer
    permission_classes = (ProjectUpdatePermission,)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_update:
            project_update = obj.update()
            if not project_update:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            else:
                data = OrderedDict()
                data['project_update'] = project_update.id
                data.update(ProjectUpdateSerializer(project_update, context=self.get_serializer_context()).to_representation(project_update))
                headers = {'Location': project_update.get_absolute_url(request=request)}
                return Response(data,
                                headers=headers,
                                status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class ProjectUpdateList(ListAPIView):

    model = ProjectUpdate
    serializer_class = ProjectUpdateListSerializer


class ProjectUpdateDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = ProjectUpdate
    serializer_class = ProjectUpdateDetailSerializer


class ProjectUpdateEventsList(SubListAPIView):

    model = ProjectUpdateEvent
    serializer_class = ProjectUpdateEventSerializer
    parent_model = ProjectUpdate
    relationship = 'project_update_events'
    view_name = _('Project Update Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(ProjectUpdateEventsList, self).finalize_response(request, response, *args, **kwargs)


class SystemJobEventsList(SubListAPIView):

    model = SystemJobEvent
    serializer_class = SystemJobEventSerializer
    parent_model = SystemJob
    relationship = 'system_job_events'
    view_name = _('System Job Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(SystemJobEventsList, self).finalize_response(request, response, *args, **kwargs)




class ProjectUpdateCancel(RetrieveAPIView):

    model = ProjectUpdate
    obj_permission_type = 'cancel'
    serializer_class = ProjectUpdateCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class ProjectUpdateNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = ProjectUpdate
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class ProjectUpdateScmInventoryUpdates(SubListAPIView):

    view_name = _("Project Update SCM Inventory Updates")
    model = InventoryUpdate
    serializer_class = InventoryUpdateListSerializer
    parent_model = ProjectUpdate
    relationship = 'scm_inventory_updates'
    parent_key = 'source_project_update'


class ProjectAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = Project


class ProjectObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Project
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class ProjectCopy(CopyAPIView):

    model = Project
    copy_return_serializer_class = ProjectSerializer


class UserList(ListCreateAPIView):

    model = User
    serializer_class = UserSerializer
    permission_classes = (UserPermission,)

    def post(self, request, *args, **kwargs):
        ret = super(UserList, self).post( request, *args, **kwargs)
        try:
            if request.data.get('is_system_auditor', False):
                # This is a faux-field that just maps to checking the system
                # auditor role member list.. unfortunately this means we can't
                # set it on creation, and thus needs to be set here.
                user = User.objects.get(id=ret.data['id'])
                user.is_system_auditor = request.data['is_system_auditor']
                ret.data['is_system_auditor'] = request.data['is_system_auditor']
        except AttributeError as exc:
            print(exc)
            pass
        return ret


class UserMeList(ListAPIView):

    model = User
    serializer_class = UserSerializer
    view_name = _('Me')

    def get_queryset(self):
        return self.model.objects.filter(pk=self.request.user.pk)


class OAuth2ApplicationList(ListCreateAPIView):

    view_name = _("OAuth 2 Applications")

    model = OAuth2Application
    serializer_class = OAuth2ApplicationSerializer
    swagger_topic = 'Authentication'


class OAuth2ApplicationDetail(RetrieveUpdateDestroyAPIView):

    view_name = _("OAuth 2 Application Detail")

    model = OAuth2Application
    serializer_class = OAuth2ApplicationSerializer
    swagger_topic = 'Authentication'

    def update_raw_data(self, data):
        data.pop('client_secret', None)
        return super(OAuth2ApplicationDetail, self).update_raw_data(data)


class ApplicationOAuth2TokenList(SubListCreateAPIView):

    view_name = _("OAuth 2 Application Tokens")

    model = OAuth2AccessToken
    serializer_class = OAuth2TokenSerializer
    parent_model = OAuth2Application
    relationship = 'oauth2accesstoken_set'
    parent_key = 'application'
    swagger_topic = 'Authentication'


class OAuth2ApplicationActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = OAuth2Application
    relationship = 'activitystream_set'
    swagger_topic = 'Authentication'
    search_fields = ('changes',)


class OAuth2TokenList(ListCreateAPIView):

    view_name = _("OAuth2 Tokens")

    model = OAuth2AccessToken
    serializer_class = OAuth2TokenSerializer
    swagger_topic = 'Authentication'


class OAuth2UserTokenList(SubListCreateAPIView):

    view_name = _("OAuth2 User Tokens")

    model = OAuth2AccessToken
    serializer_class = OAuth2TokenSerializer
    parent_model = User
    relationship = 'main_oauth2accesstoken'
    parent_key = 'user'
    swagger_topic = 'Authentication'


class UserAuthorizedTokenList(SubListCreateAPIView):

    view_name = _("OAuth2 User Authorized Access Tokens")

    model = OAuth2AccessToken
    serializer_class = UserAuthorizedTokenSerializer
    parent_model = User
    relationship = 'oauth2accesstoken_set'
    parent_key = 'user'
    swagger_topic = 'Authentication'

    def get_queryset(self):
        return get_access_token_model().objects.filter(application__isnull=False, user=self.request.user)


class OrganizationApplicationList(SubListCreateAPIView):

    view_name = _("Organization OAuth2 Applications")

    model = OAuth2Application
    serializer_class = OAuth2ApplicationSerializer
    parent_model = Organization
    relationship = 'applications'
    parent_key = 'organization'
    swagger_topic = 'Authentication'


class UserPersonalTokenList(SubListCreateAPIView):

    view_name = _("OAuth2 Personal Access Tokens")

    model = OAuth2AccessToken
    serializer_class = UserPersonalTokenSerializer
    parent_model = User
    relationship = 'main_oauth2accesstoken'
    parent_key = 'user'
    swagger_topic = 'Authentication'

    def get_queryset(self):
        return get_access_token_model().objects.filter(application__isnull=True, user=self.request.user)


class OAuth2TokenDetail(RetrieveUpdateDestroyAPIView):

    view_name = _("OAuth Token Detail")

    model = OAuth2AccessToken
    serializer_class = OAuth2TokenDetailSerializer
    swagger_topic = 'Authentication'


class OAuth2TokenActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = OAuth2AccessToken
    relationship = 'activitystream_set'
    swagger_topic = 'Authentication'
    search_fields = ('changes',)


class UserTeamsList(SubListAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = User

    def get_queryset(self):
        u = get_object_or_404(User, pk=self.kwargs['pk'])
        if not self.request.user.can_access(User, 'read', u):
            raise PermissionDenied()
        return Team.accessible_objects(self.request.user, 'read_role').filter(
            Q(member_role__members=u) | Q(admin_role__members=u)).distinct()


class UserRolesList(SubListAttachDetachAPIView):

    model = Role
    serializer_class = RoleSerializerWithParentAccess
    metadata_class = RoleMetadata
    parent_model = User
    relationship='roles'
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        u = get_object_or_404(User, pk=self.kwargs['pk'])
        if not self.request.user.can_access(User, 'read', u):
            raise PermissionDenied()
        content_type = ContentType.objects.get_for_model(User)

        return Role.filter_visible_roles(self.request.user, u.roles.all()) \
                   .exclude(content_type=content_type, object_id=u.id)

    def post(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if not sub_id:
            return super(UserRolesList, self).post(request)

        user = get_object_or_400(User, pk=self.kwargs['pk'])
        role = get_object_or_400(Role, pk=sub_id)

        credential_content_type = ContentType.objects.get_for_model(Credential)
        if role.content_type == credential_content_type:
            if role.content_object.organization and user not in role.content_object.organization.member_role:
                data = dict(msg=_("You cannot grant credential access to a user not in the credentials' organization"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            if not role.content_object.organization and not request.user.is_superuser:
                data = dict(msg=_("You cannot grant private credential access to another user"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)


        return super(UserRolesList, self).post(request, *args, **kwargs)

    def check_parent_access(self, parent=None):
        # We hide roles that shouldn't be seen in our queryset
        return True


class UserProjectsList(SubListAPIView):

    model = Project
    serializer_class = ProjectSerializer
    parent_model = User

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        my_qs = Project.accessible_objects(self.request.user, 'read_role')
        user_qs = Project.accessible_objects(parent, 'read_role')
        return my_qs & user_qs


class UserOrganizationsList(OrganizationCountsMixin, SubListAPIView):

    model = Organization
    serializer_class = OrganizationSerializer
    parent_model = User
    relationship = 'organizations'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        my_qs = Organization.accessible_objects(self.request.user, 'read_role')
        user_qs = Organization.objects.filter(member_role__members=parent)
        return my_qs & user_qs


class UserAdminOfOrganizationsList(OrganizationCountsMixin, SubListAPIView):

    model = Organization
    serializer_class = OrganizationSerializer
    parent_model = User
    relationship = 'admin_of_organizations'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        my_qs = Organization.accessible_objects(self.request.user, 'read_role')
        user_qs = Organization.objects.filter(admin_role__members=parent)
        return my_qs & user_qs


class UserActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = User
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(actor=parent) | Q(user__in=[parent]))


class UserDetail(RetrieveUpdateDestroyAPIView):

    model = User
    serializer_class = UserSerializer

    def update_filter(self, request, *args, **kwargs):
        ''' make sure non-read-only fields that can only be edited by admins, are only edited by admins '''
        obj = self.get_object()
        can_change = request.user.can_access(User, 'change', obj, request.data)
        can_admin = request.user.can_access(User, 'admin', obj, request.data)

        su_only_edit_fields = ('is_superuser', 'is_system_auditor')
        admin_only_edit_fields = ('username', 'is_active')

        fields_to_check = ()
        if not request.user.is_superuser:
            fields_to_check += su_only_edit_fields

        if can_change and not can_admin:
            fields_to_check += admin_only_edit_fields

        bad_changes = {}
        for field in fields_to_check:
            left = getattr(obj, field, None)
            right = request.data.get(field, None)
            if left is not None and right is not None and left != right:
                bad_changes[field] = (left, right)
        if bad_changes:
            raise PermissionDenied(_('Cannot change %s.') % ', '.join(bad_changes.keys()))

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = request.user.can_access(User, 'delete', obj)
        if not can_delete:
            raise PermissionDenied(_('Cannot delete user.'))
        return super(UserDetail, self).destroy(request, *args, **kwargs)


class UserAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = User


class CredentialTypeList(ListCreateAPIView):

    model = CredentialType
    serializer_class = CredentialTypeSerializer


class CredentialTypeDetail(RetrieveUpdateDestroyAPIView):

    model = CredentialType
    serializer_class = CredentialTypeSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.managed_by_tower:
            raise PermissionDenied(detail=_("Deletion not allowed for managed credential types"))
        if instance.credentials.exists():
            raise PermissionDenied(detail=_("Credential types that are in use cannot be deleted"))
        return super(CredentialTypeDetail, self).destroy(request, *args, **kwargs)


class CredentialTypeCredentialList(SubListCreateAPIView):

    model = Credential
    parent_model = CredentialType
    relationship = 'credentials'
    serializer_class = CredentialSerializer


class CredentialTypeActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = CredentialType
    relationship = 'activitystream_set'
    search_fields = ('changes',)


# remove in 3.3
class CredentialViewMixin(object):

    @property
    def related_search_fields(self):
        ret = super(CredentialViewMixin, self).related_search_fields
        if get_request_version(self.request) == 1 and 'credential_type__search' in ret:
            ret.remove('credential_type__search')
        return ret


class CredentialList(CredentialViewMixin, ListCreateAPIView):

    model = Credential
    serializer_class = CredentialSerializerCreate
    filter_backends = ListCreateAPIView.filter_backends + [V1CredentialFilterBackend]


class CredentialOwnerUsersList(SubListAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Credential
    relationship = 'admin_role.members'


class CredentialOwnerTeamsList(SubListAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = Credential

    def get_queryset(self):
        credential = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        if not self.request.user.can_access(Credential, 'read', credential):
            raise PermissionDenied()

        content_type = ContentType.objects.get_for_model(self.model)
        teams = [c.content_object.pk for c in credential.admin_role.parents.filter(content_type=content_type)]

        return self.model.objects.filter(pk__in=teams)


class UserCredentialsList(CredentialViewMixin, SubListCreateAPIView):

    model = Credential
    serializer_class = UserCredentialSerializerCreate
    parent_model = User
    parent_key = 'user'
    filter_backends = SubListCreateAPIView.filter_backends + [V1CredentialFilterBackend]

    def get_queryset(self):
        user = self.get_parent_object()
        self.check_parent_access(user)

        visible_creds = Credential.accessible_objects(self.request.user, 'read_role')
        user_creds = Credential.accessible_objects(user, 'read_role')
        return user_creds & visible_creds


class TeamCredentialsList(CredentialViewMixin, SubListCreateAPIView):

    model = Credential
    serializer_class = TeamCredentialSerializerCreate
    parent_model = Team
    parent_key = 'team'
    filter_backends = SubListCreateAPIView.filter_backends + [V1CredentialFilterBackend]

    def get_queryset(self):
        team = self.get_parent_object()
        self.check_parent_access(team)

        visible_creds = Credential.accessible_objects(self.request.user, 'read_role')
        team_creds = Credential.objects.filter(Q(use_role__parents=team.member_role) | Q(admin_role__parents=team.member_role))
        return (team_creds & visible_creds).distinct()


class OrganizationCredentialList(CredentialViewMixin, SubListCreateAPIView):

    model = Credential
    serializer_class = OrganizationCredentialSerializerCreate
    parent_model = Organization
    parent_key = 'organization'
    filter_backends = SubListCreateAPIView.filter_backends + [V1CredentialFilterBackend]

    def get_queryset(self):
        organization = self.get_parent_object()
        self.check_parent_access(organization)

        user_visible = Credential.accessible_objects(self.request.user, 'read_role').all()
        org_set = Credential.accessible_objects(organization.admin_role, 'read_role').all()

        if self.request.user.is_superuser or self.request.user.is_system_auditor:
            return org_set

        return org_set & user_visible


class CredentialDetail(RetrieveUpdateDestroyAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    filter_backends = RetrieveUpdateDestroyAPIView.filter_backends + [V1CredentialFilterBackend]


class CredentialActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Credential
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class CredentialAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = Credential


class CredentialObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Credential
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class CredentialCopy(CopyAPIView):

    model = Credential
    copy_return_serializer_class = CredentialSerializer


class HostRelatedSearchMixin(object):

    @property
    def related_search_fields(self):
        # Edge-case handle: https://github.com/ansible/ansible-tower/issues/7712
        ret = super(HostRelatedSearchMixin, self).related_search_fields
        ret.append('ansible_facts')
        return ret


class HostList(HostRelatedSearchMixin, ListCreateAPIView):

    always_allow_superuser = False
    model = Host
    serializer_class = HostSerializer

    def get_queryset(self):
        qs = super(HostList, self).get_queryset()
        filter_string = self.request.query_params.get('host_filter', None)
        if filter_string:
            filter_qs = SmartFilter.query_from_string(filter_string)
            qs &= filter_qs
        return qs.distinct()

    def list(self, *args, **kwargs):
        try:
            return super(HostList, self).list(*args, **kwargs)
        except Exception as e:
            return Response(dict(error=_(six.text_type(e))), status=status.HTTP_400_BAD_REQUEST)


class HostDetail(RelatedJobsPreventDeleteMixin, ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    always_allow_superuser = False
    model = Host
    serializer_class = HostSerializer

    def delete(self, request, *args, **kwargs):
        if self.get_object().inventory.pending_deletion:
            return Response({"error": _("The inventory for this host is already being deleted.")},
                            status=status.HTTP_400_BAD_REQUEST)
        return super(HostDetail, self).delete(request, *args, **kwargs)


class HostAnsibleFactsDetail(RetrieveAPIView):

    model = Host
    serializer_class = AnsibleFactsSerializer


class InventoryHostsList(HostRelatedSearchMixin, SubListCreateAttachDetachAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = Inventory
    relationship = 'hosts'
    parent_key = 'inventory'

    def get_queryset(self):
        inventory = self.get_parent_object()
        return getattrd(inventory, self.relationship).all()


class HostGroupsList(ControlledByScmMixin, SubListCreateAttachDetachAPIView):
    ''' the list of groups a host is directly a member of '''

    model = Group
    serializer_class = GroupSerializer
    parent_model = Host
    relationship = 'groups'

    def update_raw_data(self, data):
        data.pop('inventory', None)
        return super(HostGroupsList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject parent host inventory ID into new group data.
        data = request.data
        # HACK: Make request data mutable.
        if getattr(data, '_mutable', None) is False:
            data._mutable = True
        data['inventory'] = self.get_parent_object().inventory_id
        return super(HostGroupsList, self).create(request, *args, **kwargs)


class HostAllGroupsList(SubListAPIView):
    ''' the list of all groups of which the host is directly or indirectly a member '''

    model = Group
    serializer_class = GroupSerializer
    parent_model = Host
    relationship = 'groups'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct()
        sublist_qs = parent.all_groups.distinct()
        return qs & sublist_qs


class HostInventorySourcesList(SubListAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Host
    relationship = 'inventory_sources'


class HostSmartInventoriesList(SubListAPIView):
    model = Inventory
    serializer_class = InventorySerializer
    parent_model = Host
    relationship = 'smart_inventories'


class HostActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Host
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(host=parent) | Q(inventory=parent.inventory))


class HostFactVersionsList(SystemTrackingEnforcementMixin, ParentMixin, ListAPIView):

    model = Fact
    serializer_class = FactVersionSerializer
    parent_model = Host
    search_fields = ('facts',)
    deprecated = True

    def get_queryset(self):
        from_spec = self.request.query_params.get('from', None)
        to_spec = self.request.query_params.get('to', None)
        module_spec = self.request.query_params.get('module', None)

        if from_spec:
            from_spec = dateutil.parser.parse(from_spec)
        if to_spec:
            to_spec = dateutil.parser.parse(to_spec)

        host_obj = self.get_parent_object()

        return Fact.get_timeline(host_obj.id, module=module_spec, ts_from=from_spec, ts_to=to_spec)

    def list(self, *args, **kwargs):
        queryset = self.get_queryset() or []
        return Response(dict(results=self.serializer_class(queryset, many=True).data))


class HostFactCompareView(SystemTrackingEnforcementMixin, SubDetailAPIView):

    model = Fact
    parent_model = Host
    serializer_class = FactSerializer
    deprecated = True

    def retrieve(self, request, *args, **kwargs):
        datetime_spec = request.query_params.get('datetime', None)
        module_spec = request.query_params.get('module', "ansible")
        datetime_actual = dateutil.parser.parse(datetime_spec) if datetime_spec is not None else now()

        host_obj = self.get_parent_object()

        fact_entry = Fact.get_host_fact(host_obj.id, module_spec, datetime_actual)
        if not fact_entry:
            return Response({'detail': _('Fact not found.')}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(instance=fact_entry).data)


class HostInsights(GenericAPIView):

    model = Host
    serializer_class = EmptySerializer

    def _extract_insights_creds(self, credential):
        return (credential.inputs['username'], decrypt_field(credential, 'password'))

    def _get_insights(self, url, username, password):
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(username, password)
        headers = {'Content-Type': 'application/json'}
        return session.get(url, headers=headers, timeout=120)

    def get_insights(self, url, username, password):
        try:
            res = self._get_insights(url, username, password)
        except requests.exceptions.SSLError:
            return (dict(error=_('SSLError while trying to connect to {}').format(url)), status.HTTP_502_BAD_GATEWAY)
        except requests.exceptions.Timeout:
            return (dict(error=_('Request to {} timed out.').format(url)), status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.RequestException as e:
            return (dict(error=_('Unknown exception {} while trying to GET {}').format(e, url)), status.HTTP_502_BAD_GATEWAY)

        if res.status_code == 401:
            return (dict(error=_('Unauthorized access. Please check your Insights Credential username and password.')), status.HTTP_502_BAD_GATEWAY)
        elif res.status_code != 200:
            return (dict(error=_(
                'Failed to gather reports and maintenance plans from Insights API at URL {}. Server responded with {} status code and message {}'
            ).format(url, res.status_code, res.content)), status.HTTP_502_BAD_GATEWAY)

        try:
            filtered_insights_content = filter_insights_api_response(res.json())
            return (dict(insights_content=filtered_insights_content), status.HTTP_200_OK)
        except ValueError:
            return (dict(error=_('Expected JSON response from Insights but instead got {}').format(res.content)), status.HTTP_502_BAD_GATEWAY)

    def get(self, request, *args, **kwargs):
        host = self.get_object()
        cred = None

        if host.insights_system_id is None:
            return Response(dict(error=_('This host is not recognized as an Insights host.')), status=status.HTTP_404_NOT_FOUND)

        if host.inventory and host.inventory.insights_credential:
            cred = host.inventory.insights_credential
        else:
            return Response(dict(error=_('The Insights Credential for "{}" was not found.').format(host.inventory.name)), status=status.HTTP_404_NOT_FOUND)

        url = settings.INSIGHTS_URL_BASE + '/r/insights/v3/systems/{}/reports/'.format(host.insights_system_id)
        (username, password) = self._extract_insights_creds(cred)
        (msg, err_code) = self.get_insights(url, username, password)
        return Response(msg, status=err_code)


class GroupList(ListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer


class GroupChildrenList(ControlledByScmMixin, EnforceParentRelationshipMixin, SubListCreateAttachDetachAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Group
    relationship = 'children'
    enforce_parent_relationship = 'inventory'

    def unattach(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if sub_id is not None:
            return super(GroupChildrenList, self).unattach(request, *args, **kwargs)
        parent = self.get_parent_object()
        if not request.user.can_access(self.model, 'delete', parent):
            raise PermissionDenied()
        parent.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def is_valid_relation(self, parent, sub, created=False):
        # Prevent any cyclical group associations.
        parent_pks = set(parent.all_parents.values_list('pk', flat=True))
        parent_pks.add(parent.pk)
        child_pks = set(sub.all_children.values_list('pk', flat=True))
        child_pks.add(sub.pk)
        if parent_pks & child_pks:
            return {'error': _('Cyclical Group association.')}
        return None


class GroupPotentialChildrenList(SubListAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Group

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        qs = qs.filter(inventory__pk=parent.inventory.pk)
        except_pks = set([parent.pk])
        except_pks.update(parent.all_parents.values_list('pk', flat=True))
        except_pks.update(parent.all_children.values_list('pk', flat=True))
        return qs.exclude(pk__in=except_pks)


class GroupHostsList(HostRelatedSearchMixin,
                     ControlledByScmMixin,
                     SubListCreateAttachDetachAPIView):
    ''' the list of hosts directly below a group '''

    model = Host
    serializer_class = HostSerializer
    parent_model = Group
    relationship = 'hosts'

    def update_raw_data(self, data):
        data.pop('inventory', None)
        return super(GroupHostsList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        parent_group = Group.objects.get(id=self.kwargs['pk'])
        # Inject parent group inventory ID into new host data.
        request.data['inventory'] = parent_group.inventory_id
        existing_hosts = Host.objects.filter(inventory=parent_group.inventory, name=request.data.get('name', ''))
        if existing_hosts.count() > 0 and ('variables' not in request.data or
                                           request.data['variables'] == '' or
                                           request.data['variables'] == '{}' or
                                           request.data['variables'] == '---'):
            request.data['id'] = existing_hosts[0].id
            return self.attach(request, *args, **kwargs)
        return super(GroupHostsList, self).create(request, *args, **kwargs)


class GroupAllHostsList(HostRelatedSearchMixin, SubListAPIView):
    ''' the list of all hosts below a group, even including subgroups '''

    model = Host
    serializer_class = HostSerializer
    parent_model = Group
    relationship = 'hosts'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct() # need distinct for '&' operator
        sublist_qs = parent.all_hosts.distinct()
        return qs & sublist_qs


class GroupInventorySourcesList(SubListAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Group
    relationship = 'inventory_sources'


class GroupActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Group
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(group=parent) | Q(host__in=parent.hosts.all()))


class GroupDetail(RelatedJobsPreventDeleteMixin, ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    model = Group
    serializer_class = GroupSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        if get_request_version(request) == 1:  # TODO: deletion of automatic inventory_source, remove in 3.3
            try:
                obj.deprecated_inventory_source.delete()
            except Group.deprecated_inventory_source.RelatedObjectDoesNotExist:
                pass
        obj.delete_recursive()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InventoryGroupsList(SubListCreateAttachDetachAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Inventory
    relationship = 'groups'
    parent_key = 'inventory'


class InventoryRootGroupsList(SubListCreateAttachDetachAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Inventory
    relationship = 'groups'
    parent_key = 'inventory'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct() # need distinct for '&' operator
        return qs & parent.root_groups


class BaseVariableData(RetrieveUpdateAPIView):

    parser_classes = api_settings.DEFAULT_PARSER_CLASSES + [YAMLParser]
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [YAMLRenderer]
    is_variable_data = True # Special flag for permissions check.


class InventoryVariableData(BaseVariableData):

    model = Inventory
    serializer_class = InventoryVariableDataSerializer


class HostVariableData(BaseVariableData):

    model = Host
    serializer_class = HostVariableDataSerializer


class GroupVariableData(BaseVariableData):

    model = Group
    serializer_class = GroupVariableDataSerializer


class InventoryScriptView(RetrieveAPIView):

    model = Inventory
    serializer_class = InventoryScriptSerializer
    permission_classes = (TaskPermission,)
    filter_backends = ()

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        hostname = request.query_params.get('host', '')
        hostvars = bool(request.query_params.get('hostvars', ''))
        towervars = bool(request.query_params.get('towervars', ''))
        show_all = bool(request.query_params.get('all', ''))
        subset = request.query_params.get('subset', '')
        if subset:
            if not isinstance(subset, six.string_types):
                raise ParseError(_('Inventory subset argument must be a string.'))
            if subset.startswith('slice'):
                slice_number, slice_count = Inventory.parse_slice_params(subset)
            else:
                raise ParseError(_('Subset does not use any supported syntax.'))
        else:
            slice_number, slice_count = 1, 1
        if hostname:
            hosts_q = dict(name=hostname)
            if not show_all:
                hosts_q['enabled'] = True
            host = get_object_or_404(obj.hosts, **hosts_q)
            return Response(host.variables_dict)
        return Response(obj.get_script_data(
            hostvars=hostvars,
            towervars=towervars,
            show_all=show_all,
            slice_number=slice_number, slice_count=slice_count
        ))


class InventoryTreeView(RetrieveAPIView):

    model = Inventory
    serializer_class = GroupTreeSerializer
    filter_backends = ()

    def _populate_group_children(self, group_data, all_group_data_map, group_children_map):
        if 'children' in group_data:
            return
        group_data['children'] = []
        for child_id in group_children_map.get(group_data['id'], set()):
            group_data['children'].append(all_group_data_map[child_id])
        group_data['children'].sort(key=lambda x: x['name'])
        for child_data in group_data['children']:
            self._populate_group_children(child_data, all_group_data_map, group_children_map)

    def retrieve(self, request, *args, **kwargs):
        inventory = self.get_object()
        group_children_map = inventory.get_group_children_map()
        root_group_pks = inventory.root_groups.order_by('name').values_list('pk', flat=True)
        groups_qs = inventory.groups
        groups_qs = groups_qs.prefetch_related('inventory_sources')
        all_group_data = GroupSerializer(groups_qs, many=True).data
        all_group_data_map = dict((x['id'], x) for x in all_group_data)
        tree_data = [all_group_data_map[x] for x in root_group_pks]
        for group_data in tree_data:
            self._populate_group_children(group_data, all_group_data_map,
                                          group_children_map)
        return Response(tree_data)


class InventoryInventorySourcesList(SubListCreateAPIView):

    view_name = _('Inventory Source List')

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Inventory
    # Sometimes creation blocked by SCM inventory source restrictions
    always_allow_superuser = False
    relationship = 'inventory_sources'
    parent_key = 'inventory'


class InventoryInventorySourcesUpdate(RetrieveAPIView):
    view_name = _('Inventory Sources Update')

    model = Inventory
    obj_permission_type = 'start'
    serializer_class = InventorySourceUpdateSerializer
    permission_classes = (InventoryInventorySourcesUpdatePermission,)

    def retrieve(self, request, *args, **kwargs):
        inventory = self.get_object()
        update_data = []
        for inventory_source in inventory.inventory_sources.exclude(source=''):
            details = {'inventory_source': inventory_source.pk,
                       'can_update': inventory_source.can_update}
            update_data.append(details)
        return Response(update_data)

    def post(self, request, *args, **kwargs):
        inventory = self.get_object()
        update_data = []
        successes = 0
        failures = 0
        for inventory_source in inventory.inventory_sources.exclude(source=''):
            details = OrderedDict()
            details['inventory_source'] = inventory_source.pk
            details['status'] = None
            if inventory_source.can_update:
                update = inventory_source.update()
                details.update(InventoryUpdateSerializer(update, context=self.get_serializer_context()).to_representation(update))
                details['status'] = 'started'
                details['inventory_update'] = update.id
                successes += 1
            else:
                if not details.get('status'):
                    details['status'] = _('Could not start because `can_update` returned False')
                failures += 1
            update_data.append(details)
        if failures and successes:
            status_code = status.HTTP_202_ACCEPTED
        elif failures and not successes:
            status_code = status.HTTP_400_BAD_REQUEST
        elif not failures and not successes:
            return Response({'detail': _('No inventory sources to update.')},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            status_code = status.HTTP_200_OK
        return Response(update_data, status=status_code)


class InventorySourceList(ListCreateAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    always_allow_superuser = False

    @property
    def allowed_methods(self):
        methods = super(InventorySourceList, self).allowed_methods
        if get_request_version(getattr(self, 'request', None)) == 1:
            methods.remove('POST')
        return methods


class InventorySourceDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer


class InventorySourceSchedulesList(SubListCreateAPIView):

    view_name = _("Inventory Source Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = InventorySource
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class InventorySourceActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = InventorySource
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class InventorySourceNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = InventorySource
    relationship = 'notification_templates_any'

    def post(self, request, *args, **kwargs):
        parent = self.get_parent_object()
        if parent.source not in CLOUD_INVENTORY_SOURCES:
            return Response(dict(msg=_("Notification Templates can only be assigned when source is one of {}.")
                                 .format(CLOUD_INVENTORY_SOURCES, parent.source)),
                            status=status.HTTP_400_BAD_REQUEST)
        return super(InventorySourceNotificationTemplatesAnyList, self).post(request, *args, **kwargs)


class InventorySourceNotificationTemplatesErrorList(InventorySourceNotificationTemplatesAnyList):

    relationship = 'notification_templates_error'


class InventorySourceNotificationTemplatesSuccessList(InventorySourceNotificationTemplatesAnyList):

    relationship = 'notification_templates_success'


class InventorySourceHostsList(HostRelatedSearchMixin, SubListDestroyAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = InventorySource
    relationship = 'hosts'
    check_sub_obj_permission = False

    def perform_list_destroy(self, instance_list):
        # Activity stream doesn't record disassociation here anyway
        # no signals-related reason to not bulk-delete
        Host.groups.through.objects.filter(
            host__inventory_sources=self.get_parent_object()
        ).delete()
        return super(InventorySourceHostsList, self).perform_list_destroy(instance_list)


class InventorySourceGroupsList(SubListDestroyAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = InventorySource
    relationship = 'groups'
    check_sub_obj_permission = False

    def perform_list_destroy(self, instance_list):
        # Same arguments for bulk delete as with host list
        Group.hosts.through.objects.filter(
            group__inventory_sources=self.get_parent_object()
        ).delete()
        return super(InventorySourceGroupsList, self).perform_list_destroy(instance_list)


class InventorySourceUpdatesList(SubListAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateListSerializer
    parent_model = InventorySource
    relationship = 'inventory_updates'


class InventorySourceCredentialsList(SubListAttachDetachAPIView):

    parent_model = InventorySource
    model = Credential
    serializer_class = CredentialSerializer
    relationship = 'credentials'

    def is_valid_relation(self, parent, sub, created=False):
        # Inventory source credentials are exclusive with all other credentials
        # subject to change for https://github.com/ansible/awx/issues/277
        # or https://github.com/ansible/awx/issues/223
        if parent.credentials.exists():
            return {'msg': _("Source already has credential assigned.")}
        error = InventorySource.cloud_credential_validation(parent.source, sub)
        if error:
            return {'msg': error}
        return None


class InventorySourceUpdateView(RetrieveAPIView):

    model = InventorySource
    obj_permission_type = 'start'
    serializer_class = InventorySourceUpdateSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_update:
            update = obj.update()
            if not update:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            else:
                headers = {'Location': update.get_absolute_url(request=request)}
                data = OrderedDict()
                data['inventory_update'] = update.id
                data.update(InventoryUpdateSerializer(update, context=self.get_serializer_context()).to_representation(update))
                return Response(data, status=status.HTTP_202_ACCEPTED, headers=headers)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class InventoryUpdateList(ListAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateListSerializer


class InventoryUpdateDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateSerializer


class InventoryUpdateCredentialsList(SubListAPIView):

    parent_model = InventoryUpdate
    model = Credential
    serializer_class = CredentialSerializer
    relationship = 'credentials'


class InventoryUpdateCancel(RetrieveAPIView):

    model = InventoryUpdate
    obj_permission_type = 'cancel'
    serializer_class = InventoryUpdateCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class InventoryUpdateNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = InventoryUpdate
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class SystemJobTemplateList(ListAPIView):

    model = SystemJobTemplate
    serializer_class = SystemJobTemplateSerializer

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_system_auditor:
            raise PermissionDenied(_("Superuser privileges needed."))
        return super(SystemJobTemplateList, self).get(request, *args, **kwargs)


class SystemJobTemplateDetail(RetrieveAPIView):

    model = SystemJobTemplate
    serializer_class = SystemJobTemplateSerializer


class SystemJobTemplateLaunch(GenericAPIView):

    model = SystemJobTemplate
    obj_permission_type = 'start'
    serializer_class = EmptySerializer

    def get(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        new_job = obj.create_unified_job(extra_vars=request.data.get('extra_vars', {}))
        new_job.signal_start()
        data = OrderedDict()
        data['system_job'] = new_job.id
        data.update(SystemJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
        headers = {'Location': new_job.get_absolute_url(request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class SystemJobTemplateSchedulesList(SubListCreateAPIView):

    view_name = _("System Job Template Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = SystemJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class SystemJobTemplateJobsList(SubListAPIView):

    model = SystemJob
    serializer_class = SystemJobListSerializer
    parent_model = SystemJobTemplate
    relationship = 'jobs'
    parent_key = 'system_job_template'


class SystemJobTemplateNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = SystemJobTemplate
    relationship = 'notification_templates_any'


class SystemJobTemplateNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = SystemJobTemplate
    relationship = 'notification_templates_error'


class SystemJobTemplateNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = SystemJobTemplate
    relationship = 'notification_templates_success'


class JobList(ListCreateAPIView):

    model = Job
    metadata_class = JobTypeMetadata
    serializer_class = JobListSerializer

    @property
    def allowed_methods(self):
        methods = super(JobList, self).allowed_methods
        if get_request_version(getattr(self, 'request', None)) > 1:
            methods.remove('POST')
        return methods

    # NOTE: Remove in 3.3, switch ListCreateAPIView to ListAPIView
    def post(self, request, *args, **kwargs):
        if get_request_version(self.request) > 1:
            return Response({"error": _("POST not allowed for Job launching in version 2 of the api")},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super(JobList, self).post(request, *args, **kwargs)


class JobDetail(UnifiedJobDeletionMixin, RetrieveUpdateDestroyAPIView):

    model = Job
    metadata_class = JobTypeMetadata
    serializer_class = JobDetailSerializer

    # NOTE: When removing the V1 API in 3.4, delete the following four methods,
    # and let this class inherit from RetrieveDestroyAPIView instead of
    # RetrieveUpdateDestroyAPIView.
    @property
    def allowed_methods(self):
        methods = super(JobDetail, self).allowed_methods
        if get_request_version(getattr(self, 'request', None)) > 1:
            methods.remove('PUT')
            methods.remove('PATCH')
        return methods

    def put(self, request, *args, **kwargs):
        if get_request_version(self.request) > 1:
            return Response({"error": _("PUT not allowed for Job Details in version 2 of the API")},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super(JobDetail, self).put(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        if get_request_version(self.request) > 1:
            return Response({"error": _("PUT not allowed for Job Details in version 2 of the API")},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super(JobDetail, self).patch(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        # Only allow changes (PUT/PATCH) when job status is "new".
        if obj.status != 'new':
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super(JobDetail, self).update(request, *args, **kwargs)


class JobCredentialsList(SubListAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    parent_model = Job
    relationship = 'credentials'


class JobExtraCredentialsList(JobCredentialsList):

    deprecated = True

    def get_queryset(self):
        sublist_qs = super(JobExtraCredentialsList, self).get_queryset()
        sublist_qs = sublist_qs.filter(credential_type__kind__in=['cloud', 'net'])
        return sublist_qs


class JobActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Job
    relationship = 'activitystream_set'
    search_fields = ('changes',)


# TODO: remove endpoint in 3.3
class JobStart(GenericAPIView):

    model = Job
    obj_permission_type = 'start'
    serializer_class = EmptySerializer
    deprecated = True

    def v2_not_allowed(self):
        return Response({'detail': 'Action only possible through v1 API.'},
                        status=status.HTTP_404_NOT_FOUND)

    def get(self, request, *args, **kwargs):
        if get_request_version(request) > 1:
            return self.v2_not_allowed()
        obj = self.get_object()
        data = dict(
            can_start=obj.can_start,
        )
        if obj.can_start:
            data['passwords_needed_to_start'] = obj.passwords_needed_to_start
            data['ask_variables_on_launch'] = obj.ask_variables_on_launch
        return Response(data)

    def post(self, request, *args, **kwargs):
        if get_request_version(request) > 1:
            return self.v2_not_allowed()
        obj = self.get_object()
        if obj.can_start:
            result = obj.signal_start(**request.data)
            if not result:
                data = dict(passwords_needed_to_start=obj.passwords_needed_to_start)
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class JobCancel(RetrieveAPIView):

    model = Job
    obj_permission_type = 'cancel'
    serializer_class = JobCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class JobRelaunch(RetrieveAPIView):

    model = Job
    obj_permission_type = 'start'
    serializer_class = JobRelaunchSerializer

    def update_raw_data(self, data):
        data = super(JobRelaunch, self).update_raw_data(data)
        try:
            obj = self.get_object()
        except PermissionDenied:
            return data
        if obj:
            needed_passwords = obj.passwords_needed_to_start
            if needed_passwords:
                data['credential_passwords'] = {}
                for p in needed_passwords:
                    data['credential_passwords'][p] = u''
            else:
                data.pop('credential_passwords', None)
        return data

    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(JobRelaunch, self).dispatch(*args, **kwargs)

    def check_object_permissions(self, request, obj):
        if request.method == 'POST' and obj:
            relaunch_perm, messages = request.user.can_access_with_errors(self.model, 'start', obj)
            if not relaunch_perm and 'detail' in messages:
                self.permission_denied(request, message=messages['detail'])
        return super(JobRelaunch, self).check_object_permissions(request, obj)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        context = self.get_serializer_context()

        modified_data = request.data.copy()
        modified_data.setdefault('credential_passwords', {})
        for password in obj.passwords_needed_to_start:
            if password in modified_data:
                modified_data['credential_passwords'][password] = modified_data[password]

        # Note: is_valid() may modify request.data
        # It will remove any key/value pair who's key is not in the 'passwords_needed_to_start' list
        serializer = self.serializer_class(data=modified_data, context=context, instance=obj)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        copy_kwargs = {}
        retry_hosts = serializer.validated_data.get('hosts', None)
        if retry_hosts and retry_hosts != 'all':
            if obj.status in ACTIVE_STATES:
                return Response({'hosts': _(
                    'Wait until job finishes before retrying on {status_value} hosts.'
                ).format(status_value=retry_hosts)}, status=status.HTTP_400_BAD_REQUEST)
            host_qs = obj.retry_qs(retry_hosts)
            if not obj.job_events.filter(event='playbook_on_stats').exists():
                return Response({'hosts': _(
                    'Cannot retry on {status_value} hosts, playbook stats not available.'
                ).format(status_value=retry_hosts)}, status=status.HTTP_400_BAD_REQUEST)
            retry_host_list = host_qs.values_list('name', flat=True)
            if len(retry_host_list) == 0:
                return Response({'hosts': _(
                    'Cannot relaunch because previous job had 0 {status_value} hosts.'
                ).format(status_value=retry_hosts)}, status=status.HTTP_400_BAD_REQUEST)
            copy_kwargs['limit'] = ','.join(retry_host_list)
            limit_length = len(copy_kwargs['limit'])
            if limit_length > 1024:
                return Response({'limit': _(
                    'Cannot relaunch because the limit length {limit_length} exceeds the max of {limit_max}.'
                ).format(limit_length=limit_length, limit_max=1024)}, status=status.HTTP_400_BAD_REQUEST)

        new_job = obj.copy_unified_job(**copy_kwargs)
        result = new_job.signal_start(**serializer.validated_data['credential_passwords'])
        if not result:
            data = dict(msg=_('Error starting job!'))
            new_job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = JobSerializer(new_job, context=context).data
            # Add job key to match what old relaunch returned.
            data['job'] = new_job.id
            headers = {'Location': new_job.get_absolute_url(request=request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class JobCreateSchedule(RetrieveAPIView):

    model = Job
    obj_permission_type = 'start'
    serializer_class = JobCreateScheduleSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        if not obj.can_schedule:
            if getattr(obj, 'passwords_needed_to_start', None):
                return Response({"error": _('Cannot create schedule because job requires credential passwords.')},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                obj.launch_config
            except ObjectDoesNotExist:
                return Response({"error": _('Cannot create schedule because job was launched by legacy method.')},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": _('Cannot create schedule because a related resource is missing.')},
                            status=status.HTTP_400_BAD_REQUEST)

        config = obj.launch_config

        # Make up a name for the schedule, guarentee that it is unique
        name = 'Auto-generated schedule from job {}'.format(obj.id)
        existing_names = Schedule.objects.filter(name__startswith=name).values_list('name', flat=True)
        if name in existing_names:
            idx = 1
            alt_name = '{} - number {}'.format(name, idx)
            while alt_name in existing_names:
                idx += 1
                alt_name = '{} - number {}'.format(name, idx)
            name = alt_name

        schedule_data = dict(
            name=name,
            unified_job_template=obj.unified_job_template,
            enabled=False,
            rrule='{}Z RRULE:FREQ=MONTHLY;INTERVAL=1'.format(now().strftime('DTSTART:%Y%m%dT%H%M%S')),
            extra_data=config.extra_data,
            survey_passwords=config.survey_passwords,
            inventory=config.inventory,
            char_prompts=config.char_prompts,
            credentials=set(config.credentials.all())
        )
        if not request.user.can_access(Schedule, 'add', schedule_data):
            raise PermissionDenied()

        creds_list = schedule_data.pop('credentials')
        schedule = Schedule.objects.create(**schedule_data)
        schedule.credentials.add(*creds_list)

        data = ScheduleSerializer(schedule, context=self.get_serializer_context()).data
        data.serializer.instance = None  # hack to avoid permissions.py assuming this is Job model
        headers = {'Location': schedule.get_absolute_url(request=request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class JobNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = Job
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class BaseJobHostSummariesList(SubListAPIView):

    model = JobHostSummary
    serializer_class = JobHostSummarySerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_host_summaries'
    view_name = _('Job Host Summaries List')
    search_fields = ('host_name',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).select_related('job', 'job__job_template', 'host')


class HostJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Host


class GroupJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Group


class JobJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Job


class JobHostSummaryDetail(RetrieveAPIView):

    model = JobHostSummary
    serializer_class = JobHostSummarySerializer


class JobEventList(ListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    search_fields = ('stdout',)


class JobEventDetail(RetrieveAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer


class JobEventChildrenList(SubListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    parent_model = JobEvent
    relationship = 'children'
    view_name = _('Job Event Children List')
    search_fields = ('stdout',)


class JobEventHostsList(HostRelatedSearchMixin, SubListAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = JobEvent
    relationship = 'hosts'
    view_name = _('Job Event Hosts List')


class BaseJobEventsList(SubListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_events'
    view_name = _('Job Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(BaseJobEventsList, self).finalize_response(request, response, *args, **kwargs)


class HostJobEventsList(BaseJobEventsList):

    parent_model = Host

    def get_queryset(self):
        parent_obj = self.get_parent_object()
        self.check_parent_access(parent_obj)
        qs = self.request.user.get_queryset(self.model).filter(
            Q(host=parent_obj) | Q(hosts=parent_obj)).distinct()
        return qs


class GroupJobEventsList(BaseJobEventsList):

    parent_model = Group


class JobJobEventsList(BaseJobEventsList):

    parent_model = Job

    def get_queryset(self):
        job = self.get_parent_object()
        self.check_parent_access(job)
        qs = job.job_events
        qs = qs.select_related('host')
        qs = qs.prefetch_related('hosts', 'children')
        return qs.all()


class AdHocCommandList(ListCreateAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandListSerializer
    always_allow_superuser = False

    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(AdHocCommandList, self).dispatch(*args, **kwargs)

    def update_raw_data(self, data):
        # Hide inventory and limit fields from raw data, since they will be set
        # automatically by sub list create view.
        parent_model = getattr(self, 'parent_model', None)
        if parent_model in (Host, Group):
            data.pop('inventory', None)
            data.pop('limit', None)
        return super(AdHocCommandList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject inventory ID and limit if parent objects is a host/group.
        if hasattr(self, 'get_parent_object') and not getattr(self, 'parent_key', None):
            data = request.data
            # HACK: Make request data mutable.
            if getattr(data, '_mutable', None) is False:
                data._mutable = True
            parent_obj = self.get_parent_object()
            if isinstance(parent_obj, (Host, Group)):
                data['inventory'] = parent_obj.inventory_id
                data['limit'] = parent_obj.name

        # Check for passwords needed before creating ad hoc command.
        credential_pk = get_pk_from_dict(request.data, 'credential')
        if credential_pk:
            credential = get_object_or_400(Credential, pk=credential_pk)
            needed = credential.passwords_needed
            provided = dict([(field, request.data.get(field, '')) for field in needed])
            if not all(provided.values()):
                data = dict(passwords_needed_to_start=needed)
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        response = super(AdHocCommandList, self).create(request, *args, **kwargs)
        if response.status_code != status.HTTP_201_CREATED:
            return response

        # Start ad hoc command running when created.
        ad_hoc_command = get_object_or_400(self.model, pk=response.data['id'])
        result = ad_hoc_command.signal_start(**request.data)
        if not result:
            data = dict(passwords_needed_to_start=ad_hoc_command.passwords_needed_to_start)
            ad_hoc_command.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return response


class InventoryAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = Inventory
    relationship = 'ad_hoc_commands'
    parent_key = 'inventory'


class GroupAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = Group
    relationship = 'ad_hoc_commands'


class HostAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = Host
    relationship = 'ad_hoc_commands'


class AdHocCommandDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandDetailSerializer


class AdHocCommandCancel(RetrieveAPIView):

    model = AdHocCommand
    obj_permission_type = 'cancel'
    serializer_class = AdHocCommandCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class AdHocCommandRelaunch(GenericAPIView):

    model = AdHocCommand
    obj_permission_type = 'start'
    serializer_class = AdHocCommandRelaunchSerializer

    # FIXME: Figure out why OPTIONS request still shows all fields.

    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(AdHocCommandRelaunch, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = dict(passwords_needed_to_start=obj.passwords_needed_to_start)
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        # Re-validate ad hoc command against serializer to check if module is
        # still allowed.
        data = {}
        for field in ('job_type', 'inventory_id', 'limit', 'credential_id',
                      'module_name', 'module_args', 'forks', 'verbosity',
                      'extra_vars', 'become_enabled'):
            if field.endswith('_id'):
                data[field[:-3]] = getattr(obj, field)
            else:
                data[field] = getattr(obj, field)
        serializer = AdHocCommandSerializer(data=data, context=self.get_serializer_context())
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        # Check for passwords needed before copying ad hoc command.
        needed = obj.passwords_needed_to_start
        provided = dict([(field, request.data.get(field, '')) for field in needed])
        if not all(provided.values()):
            data = dict(passwords_needed_to_start=needed)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Copy and start the new ad hoc command.
        new_ad_hoc_command = obj.copy()
        result = new_ad_hoc_command.signal_start(**request.data)
        if not result:
            data = dict(passwords_needed_to_start=new_ad_hoc_command.passwords_needed_to_start)
            new_ad_hoc_command.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = AdHocCommandSerializer(new_ad_hoc_command, context=self.get_serializer_context()).data
            # Add ad_hoc_command key to match what was previously returned.
            data['ad_hoc_command'] = new_ad_hoc_command.id
            headers = {'Location': new_ad_hoc_command.get_absolute_url(request=request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class AdHocCommandEventList(ListAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    search_fields = ('stdout',)


class AdHocCommandEventDetail(RetrieveAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer


class BaseAdHocCommandEventsList(SubListAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'ad_hoc_command_events'
    view_name = _('Ad Hoc Command Events List')
    search_fields = ('stdout',)


class HostAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = Host


#class GroupJobEventsList(BaseJobEventsList):
#    parent_model = Group


class AdHocCommandAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = AdHocCommand


class AdHocCommandActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = AdHocCommand
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class AdHocCommandNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = AdHocCommand
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class SystemJobList(ListCreateAPIView):

    model = SystemJob
    serializer_class = SystemJobListSerializer

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_system_auditor:
            raise PermissionDenied(_("Superuser privileges needed."))
        return super(SystemJobList, self).get(request, *args, **kwargs)


class SystemJobDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = SystemJob
    serializer_class = SystemJobSerializer


class SystemJobCancel(RetrieveAPIView):

    model = SystemJob
    obj_permission_type = 'cancel'
    serializer_class = SystemJobCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class SystemJobNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = SystemJob
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class UnifiedJobTemplateList(ListAPIView):

    model = UnifiedJobTemplate
    serializer_class = UnifiedJobTemplateSerializer


class UnifiedJobList(ListAPIView):

    model = UnifiedJob
    serializer_class = UnifiedJobListSerializer


def redact_ansi(line):
    # Remove ANSI escape sequences used to embed event data.
    line = re.sub(r'\x1b\[K(?:[A-Za-z0-9+/=]+\x1b\[\d+D)+\x1b\[K', '', line)
    # Remove ANSI color escape sequences.
    return re.sub(r'\x1b[^m]*m', '', line)


class StdoutFilter(object):

    def __init__(self, fileobj):
        self._functions = []
        self.fileobj = fileobj
        self.extra_data = ''
        if hasattr(fileobj, 'close'):
            self.close = fileobj.close

    def read(self, size=-1):
        data = self.extra_data
        while size > 0 and len(data) < size:
            line = self.fileobj.readline(size)
            if not line:
                break
            line = self.process_line(line)
            data += line
        if size > 0 and len(data) > size:
            self.extra_data = data[size:]
            data = data[:size]
        else:
            self.extra_data = ''
        return data

    def register(self, func):
        self._functions.append(func)

    def process_line(self, line):
        for func in self._functions:
            line = func(line)
        return line


class UnifiedJobStdout(RetrieveAPIView):

    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    serializer_class = UnifiedJobStdoutSerializer
    renderer_classes = [BrowsableAPIRenderer, renderers.StaticHTMLRenderer,
                        PlainTextRenderer, AnsiTextRenderer,
                        renderers.JSONRenderer, DownloadTextRenderer, AnsiDownloadRenderer]
    filter_backends = ()

    def retrieve(self, request, *args, **kwargs):
        unified_job = self.get_object()
        try:
            target_format = request.accepted_renderer.format
            if target_format in ('html', 'api', 'json'):
                content_encoding = request.query_params.get('content_encoding', None)
                start_line = request.query_params.get('start_line', 0)
                end_line = request.query_params.get('end_line', None)
                dark_val = request.query_params.get('dark', '')
                dark = bool(dark_val and dark_val[0].lower() in ('1', 't', 'y'))
                content_only = bool(target_format in ('api', 'json'))
                dark_bg = (content_only and dark) or (not content_only and (dark or not dark_val))
                content, start, end, absolute_end = unified_job.result_stdout_raw_limited(start_line, end_line)

                # Remove any ANSI escape sequences containing job event data.
                content = re.sub(r'\x1b\[K(?:[A-Za-z0-9+/=]+\x1b\[\d+D)+\x1b\[K', '', content)

                body = ansiconv.to_html(cgi.escape(content))

                context = {
                    'title': get_view_name(self.__class__),
                    'body': mark_safe(body),
                    'dark': dark_bg,
                    'content_only': content_only,
                }
                data = render_to_string('api/stdout.html', context).strip()

                if target_format == 'api':
                    return Response(mark_safe(data))
                if target_format == 'json':
                    content = content.encode('utf-8')
                    if content_encoding == 'base64':
                        content = b64encode(content)
                    return Response({'range': {'start': start, 'end': end, 'absolute_end': absolute_end}, 'content': content})
                return Response(data)
            elif target_format == 'txt':
                return Response(unified_job.result_stdout)
            elif target_format == 'ansi':
                return Response(unified_job.result_stdout_raw)
            elif target_format in {'txt_download', 'ansi_download'}:
                filename = '{type}_{pk}{suffix}.txt'.format(
                    type=camelcase_to_underscore(unified_job.__class__.__name__),
                    pk=unified_job.id,
                    suffix='.ansi' if target_format == 'ansi_download' else ''
                )
                content_fd = unified_job.result_stdout_raw_handle(enforce_max_bytes=False)
                redactor = StdoutFilter(content_fd)
                if target_format == 'txt_download':
                    redactor.register(redact_ansi)
                if type(unified_job) == ProjectUpdate:
                    redactor.register(UriCleaner.remove_sensitive)
                response = HttpResponse(FileWrapper(redactor), content_type='text/plain')
                response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
                return response
            else:
                return super(UnifiedJobStdout, self).retrieve(request, *args, **kwargs)
        except StdoutMaxBytesExceeded as e:
            response_message = _(
                "Standard Output too large to display ({text_size} bytes), "
                "only download supported for sizes over {supported_size} bytes.").format(
                    text_size=e.total, supported_size=e.supported
            )
            if request.accepted_renderer.format == 'json':
                return Response({'range': {'start': 0, 'end': 1, 'absolute_end': 1}, 'content': response_message})
            else:
                return Response(response_message)


class ProjectUpdateStdout(UnifiedJobStdout):

    model = ProjectUpdate


class InventoryUpdateStdout(UnifiedJobStdout):

    model = InventoryUpdate


class JobStdout(UnifiedJobStdout):

    model = Job


class AdHocCommandStdout(UnifiedJobStdout):

    model = AdHocCommand


class NotificationTemplateList(ListCreateAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer


class NotificationTemplateDetail(RetrieveUpdateDestroyAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if obj.notifications.filter(status='pending').exists():
            return Response({"error": _("Delete not allowed while there are pending notifications")},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super(NotificationTemplateDetail, self).delete(request, *args, **kwargs)


class NotificationTemplateTest(GenericAPIView):
    '''Test a Notification Template'''

    view_name = _('Notification Template Test')
    model = NotificationTemplate
    obj_permission_type = 'start'
    serializer_class = EmptySerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        notification = obj.generate_notification("Tower Notification Test {} {}".format(obj.id, settings.TOWER_URL_BASE),
                                                 {"body": "Ansible Tower Test Notification {} {}".format(obj.id, settings.TOWER_URL_BASE)})
        if not notification:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        else:
            connection.on_commit(lambda: send_notifications.delay([notification.id]))
            data = OrderedDict()
            data['notification'] = notification.id
            data.update(NotificationSerializer(notification, context=self.get_serializer_context()).to_representation(notification))
            headers = {'Location': notification.get_absolute_url(request=request)}
            return Response(data,
                            headers=headers,
                            status=status.HTTP_202_ACCEPTED)


class NotificationTemplateNotificationList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = NotificationTemplate
    relationship = 'notifications'
    parent_key = 'notification_template'
    search_fields = ('subject', 'notification_type', 'body',)


class NotificationTemplateCopy(CopyAPIView):

    model = NotificationTemplate
    copy_return_serializer_class = NotificationTemplateSerializer


class NotificationList(ListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    search_fields = ('subject', 'notification_type', 'body',)


class NotificationDetail(RetrieveAPIView):

    model = Notification
    serializer_class = NotificationSerializer


class ActivityStreamList(ActivityStreamEnforcementMixin, SimpleListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    search_fields = ('changes',)


class ActivityStreamDetail(ActivityStreamEnforcementMixin, RetrieveAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer


class RoleList(ListAPIView):

    model = Role
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        result = Role.visible_roles(self.request.user)
        # Sanity check: is the requesting user an orphaned non-admin/auditor?
        # if yes, make system admin/auditor mandatorily visible.
        if not self.request.user.organizations.exists() and\
           not self.request.user.is_superuser and\
           not self.request.user.is_system_auditor:
            mandatories = ('system_administrator', 'system_auditor')
            super_qs = Role.objects.filter(singleton_name__in=mandatories)
            result = result | super_qs
        return result


class RoleDetail(RetrieveAPIView):

    model = Role
    serializer_class = RoleSerializer


class RoleUsersList(SubListAttachDetachAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Role
    relationship = 'members'

    def get_queryset(self):
        role = self.get_parent_object()
        self.check_parent_access(role)
        return role.members.all()

    def post(self, request, *args, **kwargs):
        # Forbid implicit user creation here
        sub_id = request.data.get('id', None)
        if not sub_id:
            return super(RoleUsersList, self).post(request)

        user = get_object_or_400(User, pk=sub_id)
        role = self.get_parent_object()

        credential_content_type = ContentType.objects.get_for_model(Credential)
        if role.content_type == credential_content_type:
            if role.content_object.organization and user not in role.content_object.organization.member_role:
                data = dict(msg=_("You cannot grant credential access to a user not in the credentials' organization"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            if not role.content_object.organization and not request.user.is_superuser:
                data = dict(msg=_("You cannot grant private credential access to another user"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        return super(RoleUsersList, self).post(request, *args, **kwargs)


class RoleTeamsList(SubListAttachDetachAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = Role
    relationship = 'member_role.parents'
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        role = self.get_parent_object()
        self.check_parent_access(role)
        return Team.objects.filter(member_role__children=role)

    def post(self, request, pk, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if not sub_id:
            return super(RoleTeamsList, self).post(request)

        team = get_object_or_400(Team, pk=sub_id)
        role = Role.objects.get(pk=self.kwargs['pk'])

        organization_content_type = ContentType.objects.get_for_model(Organization)
        if role.content_type == organization_content_type and role.role_field in ['member_role', 'admin_role']:
            data = dict(msg=_("You cannot assign an Organization participation role as a child role for a Team."))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        credential_content_type = ContentType.objects.get_for_model(Credential)
        if role.content_type == credential_content_type:
            if not role.content_object.organization or role.content_object.organization.id != team.organization.id:
                data = dict(msg=_("You cannot grant credential access to a team when the Organization field isn't set, or belongs to a different organization"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        action = 'attach'
        if request.data.get('disassociate', None):
            action = 'unattach'

        if role.is_singleton() and action == 'attach':
            data = dict(msg=_("You cannot grant system-level permissions to a team."))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.can_access(self.parent_model, action, role, team,
                                       self.relationship, request.data,
                                       skip_sub_obj_read_check=False):
            raise PermissionDenied()
        if request.data.get('disassociate', None):
            team.member_role.children.remove(role)
        else:
            team.member_role.children.add(role)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleParentsList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Role
    relationship = 'parents'
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        role = Role.objects.get(pk=self.kwargs['pk'])
        return Role.filter_visible_roles(self.request.user, role.parents.all())


class RoleChildrenList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Role
    relationship = 'children'
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        role = Role.objects.get(pk=self.kwargs['pk'])
        return Role.filter_visible_roles(self.request.user, role.children.all())


# Create view functions for all of the class-based views to simplify inclusion
# in URL patterns and reverse URL lookups, converting CamelCase names to
# lowercase_with_underscore (e.g. MyView.as_view() becomes my_view).
this_module = sys.modules[__name__]
for attr, value in locals().items():
    if isinstance(value, type) and issubclass(value, APIView):
        name = camelcase_to_underscore(attr)
        view = value.as_view()
        setattr(this_module, name, view)
