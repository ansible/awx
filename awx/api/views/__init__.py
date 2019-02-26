# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import cgi
import dateutil
import functools
import logging
import re
import requests
import socket
import sys
import time
from base64 import b64encode
from collections import OrderedDict, Iterable


# Django
from django.conf import settings
from django.core.exceptions import FieldError, ObjectDoesNotExist
from django.db.models import Q, Sum
from django.db import IntegrityError, transaction, connection
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


# Django REST Framework
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.parsers import FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer, StaticHTMLRenderer
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
from awx.api.generics import (
    APIView, BaseUsersList, CopyAPIView, DeleteLastUnattachLabelMixin,
    GenericAPIView, ListAPIView, ListCreateAPIView, ParentMixin,
    ResourceAccessList, RetrieveAPIView, RetrieveDestroyAPIView,
    RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, SimpleListAPIView,
    SubDetailAPIView, SubListAPIView, SubListAttachDetachAPIView,
    SubListCreateAPIView, SubListCreateAttachDetachAPIView,
    SubListDestroyAPIView, get_view_name
)
from awx.api.versioning import reverse, get_request_version
from awx.conf.license import feature_enabled, feature_exists, LicenseForbids, get_license
from awx.main import models
from awx.main.utils import (
    camelcase_to_underscore,
    extract_ansible_vars,
    get_awx_version,
    get_object_or_400,
    getattrd,
    get_pk_from_dict,
    schedule_task_manager,
)
from awx.main.utils.encryption import encrypt_value
from awx.main.utils.filters import SmartFilter
from awx.main.utils.insights import filter_insights_api_response
from awx.main.redact import UriCleaner
from awx.api.permissions import (
    JobTemplateCallbackPermission, TaskPermission, ProjectUpdatePermission,
    InventoryInventorySourcesUpdatePermission, UserPermission,
    InstanceGroupTowerPermission,
)
from awx.api import renderers
from awx.api import serializers
from awx.api.metadata import RoleMetadata, JobTypeMetadata
from awx.main.constants import ACTIVE_STATES
from awx.main.scheduler.dag_workflow import WorkflowDAG
from awx.api.views.mixin import (
    ActivityStreamEnforcementMixin, ControlledByScmMixin,
    InstanceGroupMembershipMixin, OrganizationCountsMixin,
    RelatedJobsPreventDeleteMixin, SystemTrackingEnforcementMixin,
    UnifiedJobDeletionMixin, WorkflowsEnforcementMixin,
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
from awx.api.views.root import ( # noqa
    ApiRootView,
    ApiOAuthAuthorizationRootView,
    ApiVersionRootView,
    ApiV1RootView,
    ApiV2RootView,
    ApiV1PingView,
    ApiV1ConfigView,
)


logger = logging.getLogger('awx.api.views')


def api_exception_handler(exc, context):
    '''
    Override default API exception handler to catch IntegrityError exceptions.
    '''
    if isinstance(exc, IntegrityError):
        exc = ParseError(exc.args[0])
    if isinstance(exc, FieldError):
        exc = ParseError(exc.args[0])
    if isinstance(context['view'], UnifiedJobStdout):
        context['view'].renderer_classes = [renderers.BrowsableAPIRenderer, JSONRenderer]
    return exception_handler(exc, context)


class DashboardView(APIView):

    view_name = _("Dashboard")
    swagger_topic = 'Dashboard'

    def get(self, request, format=None):
        ''' Show Dashboard Details '''
        data = OrderedDict()
        data['related'] = {'jobs_graph': reverse('api:dashboard_jobs_graph_view', request=request)}
        user_inventory = get_user_queryset(request.user, models.Inventory)
        inventory_with_failed_hosts = user_inventory.filter(hosts_with_active_failures__gt=0)
        user_inventory_external = user_inventory.filter(has_inventory_sources=True)
        failed_inventory = user_inventory.aggregate(Sum('inventory_sources_with_failures'))['inventory_sources_with_failures__sum']
        data['inventories'] = {'url': reverse('api:inventory_list', request=request),
                               'total': user_inventory.count(),
                               'total_with_inventory_source': user_inventory_external.count(),
                               'job_failed': inventory_with_failed_hosts.count(),
                               'inventory_failed': failed_inventory}
        user_inventory_sources = get_user_queryset(request.user, models.InventorySource)
        ec2_inventory_sources = user_inventory_sources.filter(source='ec2')
        ec2_inventory_failed = ec2_inventory_sources.filter(status='failed')
        data['inventory_sources'] = {}
        data['inventory_sources']['ec2'] = {'url': reverse('api:inventory_source_list', request=request) + "?source=ec2",
                                            'failures_url': reverse('api:inventory_source_list', request=request) + "?source=ec2&status=failed",
                                            'label': 'Amazon EC2',
                                            'total': ec2_inventory_sources.count(),
                                            'failed': ec2_inventory_failed.count()}

        user_groups = get_user_queryset(request.user, models.Group)
        groups_job_failed = (
            models.Group.objects.filter(hosts_with_active_failures__gt=0) | models.Group.objects.filter(groups_with_active_failures__gt=0)
        ).count()
        groups_inventory_failed = models.Group.objects.filter(inventory_sources__last_job_failed=True).count()
        data['groups'] = {'url': reverse('api:group_list', request=request),
                          'failures_url': reverse('api:group_list', request=request) + "?has_active_failures=True",
                          'total': user_groups.count(),
                          'job_failed': groups_job_failed,
                          'inventory_failed': groups_inventory_failed}

        user_hosts = get_user_queryset(request.user, models.Host)
        user_hosts_failed = user_hosts.filter(has_active_failures=True)
        data['hosts'] = {'url': reverse('api:host_list', request=request),
                         'failures_url': reverse('api:host_list', request=request) + "?has_active_failures=True",
                         'total': user_hosts.count(),
                         'failed': user_hosts_failed.count()}

        user_projects = get_user_queryset(request.user, models.Project)
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

        user_jobs = get_user_queryset(request.user, models.Job)
        user_failed_jobs = user_jobs.filter(failed=True)
        data['jobs'] = {'url': reverse('api:job_list', request=request),
                        'failure_url': reverse('api:job_list', request=request) + "?failed=True",
                        'total': user_jobs.count(),
                        'failed': user_failed_jobs.count()}

        user_list = get_user_queryset(request.user, models.User)
        team_list = get_user_queryset(request.user, models.Team)
        credential_list = get_user_queryset(request.user, models.Credential)
        job_template_list = get_user_queryset(request.user, models.JobTemplate)
        organization_list = get_user_queryset(request.user, models.Organization)
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

        user_unified_jobs = get_user_queryset(request.user, models.UnifiedJob)

        success_query = user_unified_jobs.filter(status='successful')
        failed_query = user_unified_jobs.filter(status='failed')

        if job_type == 'inv_sync':
            success_query = success_query.filter(instance_of=models.InventoryUpdate)
            failed_query = failed_query.filter(instance_of=models.InventoryUpdate)
        elif job_type == 'playbook_run':
            success_query = success_query.filter(instance_of=models.Job)
            failed_query = failed_query.filter(instance_of=models.Job)
        elif job_type == 'scm_update':
            success_query = success_query.filter(instance_of=models.ProjectUpdate)
            failed_query = failed_query.filter(instance_of=models.ProjectUpdate)

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
    model = models.Instance
    serializer_class = serializers.InstanceSerializer
    search_fields = ('hostname',)


class InstanceDetail(RetrieveUpdateAPIView):

    view_name = _("Instance Detail")
    model = models.Instance
    serializer_class = serializers.InstanceSerializer


    def update(self, request, *args, **kwargs):
        r = super(InstanceDetail, self).update(request, *args, **kwargs)
        if status.is_success(r.status_code):
            obj = self.get_object()
            if obj.enabled:
                obj.refresh_capacity()
            else:
                obj.capacity = 0
            obj.save()
            r.data = serializers.InstanceSerializer(obj, context=self.get_serializer_context()).to_representation(obj)
        return r


class InstanceUnifiedJobsList(SubListAPIView):

    view_name = _("Instance Jobs")
    model = models.UnifiedJob
    serializer_class = serializers.UnifiedJobListSerializer
    parent_model = models.Instance

    def get_queryset(self):
        po = self.get_parent_object()
        qs = get_user_queryset(self.request.user, models.UnifiedJob)
        qs = qs.filter(execution_node=po.hostname)
        return qs


class InstanceInstanceGroupsList(InstanceGroupMembershipMixin, SubListCreateAttachDetachAPIView):

    view_name = _("Instance's Instance Groups")
    model = models.InstanceGroup
    serializer_class = serializers.InstanceGroupSerializer
    parent_model = models.Instance
    relationship = 'rampart_groups'


class InstanceGroupList(ListCreateAPIView):

    view_name = _("Instance Groups")
    model = models.InstanceGroup
    serializer_class = serializers.InstanceGroupSerializer


class InstanceGroupDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):

    always_allow_superuser = False
    view_name = _("Instance Group Detail")
    model = models.InstanceGroup
    serializer_class = serializers.InstanceGroupSerializer
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
    model = models.UnifiedJob
    serializer_class = serializers.UnifiedJobListSerializer
    parent_model = models.InstanceGroup
    relationship = "unifiedjob_set"


class InstanceGroupInstanceList(InstanceGroupMembershipMixin, SubListAttachDetachAPIView):

    view_name = _("Instance Group's Instances")
    model = models.Instance
    serializer_class = serializers.InstanceSerializer
    parent_model = models.InstanceGroup
    relationship = "instances"
    search_fields = ('hostname',)


class ScheduleList(ListCreateAPIView):

    view_name = _("Schedules")
    model = models.Schedule
    serializer_class = serializers.ScheduleSerializer


class ScheduleDetail(RetrieveUpdateDestroyAPIView):

    model = models.Schedule
    serializer_class = serializers.ScheduleSerializer


class SchedulePreview(GenericAPIView):

    model = models.Schedule
    view_name = _('Schedule Recurrence Rule Preview')
    serializer_class = serializers.SchedulePreviewSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            next_stamp = now()
            schedule = []
            gen = models.Schedule.rrulestr(serializer.validated_data['rrule']).xafter(next_stamp, count=20)

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
            for zone in models.Schedule.get_zoneinfo()
        ]
        return Response(zones)


class LaunchConfigCredentialsBase(SubListAttachDetachAPIView):

    model = models.Credential
    serializer_class = serializers.CredentialSerializer
    relationship = 'credentials'

    def is_valid_relation(self, parent, sub, created=False):
        if not parent.unified_job_template:
            return {"msg": _("Cannot assign credential when related template is null.")}

        ask_mapping = parent.unified_job_template.get_ask_mapping()

        if self.relationship not in ask_mapping:
            return {"msg": _("Related template cannot accept {} on launch.").format(self.relationship)}
        elif sub.passwords_needed:
            return {"msg": _("Credential that requires user input on launch "
                             "cannot be used in saved launch configuration.")}

        ask_field_name = ask_mapping[self.relationship]

        if not getattr(parent.unified_job_template, ask_field_name):
            return {"msg": _("Related template is not configured to accept credentials on launch.")}
        elif sub.unique_hash() in [cred.unique_hash() for cred in parent.credentials.all()]:
            return {"msg": _("This launch configuration already provides a {credential_type} credential.").format(
                credential_type=sub.unique_hash(display=True))}
        elif sub.pk in parent.unified_job_template.credentials.values_list('pk', flat=True):
            return {"msg": _("Related template already uses {credential_type} credential.").format(
                credential_type=sub.name)}

        # None means there were no validation errors
        return None


class ScheduleCredentialsList(LaunchConfigCredentialsBase):

    parent_model = models.Schedule


class ScheduleUnifiedJobsList(SubListAPIView):

    model = models.UnifiedJob
    serializer_class = serializers.UnifiedJobListSerializer
    parent_model = models.Schedule
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
        auth_backends = list(load_backends(settings.AUTHENTICATION_BACKENDS, force_load=True).items())
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

    model = models.Team
    serializer_class = serializers.TeamSerializer


class TeamDetail(RetrieveUpdateDestroyAPIView):

    model = models.Team
    serializer_class = serializers.TeamSerializer


class TeamUsersList(BaseUsersList):

    model = models.User
    serializer_class = serializers.UserSerializer
    parent_model = models.Team
    relationship = 'member_role.members'


class TeamRolesList(SubListAttachDetachAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializerWithParentAccess
    metadata_class = RoleMetadata
    parent_model = models.Team
    relationship='member_role.children'
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        team = get_object_or_404(models.Team, pk=self.kwargs['pk'])
        if not self.request.user.can_access(models.Team, 'read', team):
            raise PermissionDenied()
        return models.Role.filter_visible_roles(self.request.user, team.member_role.children.all().exclude(pk=team.read_role.pk))

    def post(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if not sub_id:
            return super(TeamRolesList, self).post(request)

        role = get_object_or_400(models.Role, pk=sub_id)
        org_content_type = ContentType.objects.get_for_model(models.Organization)
        if role.content_type == org_content_type and role.role_field in ['member_role', 'admin_role']:
            data = dict(msg=_("You cannot assign an Organization participation role as a child role for a Team."))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        if role.is_singleton():
            data = dict(msg=_("You cannot grant system-level permissions to a team."))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        team = get_object_or_404(models.Team, pk=self.kwargs['pk'])
        credential_content_type = ContentType.objects.get_for_model(models.Credential)
        if role.content_type == credential_content_type:
            if not role.content_object.organization or role.content_object.organization.id != team.organization.id:
                data = dict(msg=_("You cannot grant credential access to a team when the Organization field isn't set, or belongs to a different organization"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        return super(TeamRolesList, self).post(request, *args, **kwargs)


class TeamObjectRolesList(SubListAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer
    parent_model = models.Team
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return models.Role.objects.filter(content_type=content_type, object_id=po.pk)


class TeamProjectsList(SubListAPIView):

    model = models.Project
    serializer_class = serializers.ProjectSerializer
    parent_model = models.Team

    def get_queryset(self):
        team = self.get_parent_object()
        self.check_parent_access(team)
        model_ct = ContentType.objects.get_for_model(self.model)
        parent_ct = ContentType.objects.get_for_model(self.parent_model)
        proj_roles = models.Role.objects.filter(
            Q(ancestors__content_type=parent_ct) & Q(ancestors__object_id=team.pk),
            content_type=model_ct
        )
        return self.model.accessible_objects(self.request.user, 'read_role').filter(pk__in=[t.content_object.pk for t in proj_roles])


class TeamActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.Team
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)

        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(team=parent) |
                         Q(project__in=models.Project.accessible_objects(parent, 'read_role')) |
                         Q(credential__in=models.Credential.accessible_objects(parent, 'read_role')))


class TeamAccessList(ResourceAccessList):

    model = models.User # needs to be User for AccessLists's
    parent_model = models.Team


class ProjectList(ListCreateAPIView):

    model = models.Project
    serializer_class = serializers.ProjectSerializer

    def get_queryset(self):
        projects_qs = models.Project.accessible_objects(self.request.user, 'read_role')
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

    model = models.Project
    serializer_class = serializers.ProjectSerializer


class ProjectPlaybooks(RetrieveAPIView):

    model = models.Project
    serializer_class = serializers.ProjectPlaybooksSerializer


class ProjectInventories(RetrieveAPIView):

    model = models.Project
    serializer_class = serializers.ProjectInventoriesSerializer


class ProjectTeamsList(ListAPIView):

    model = models.Team
    serializer_class = serializers.TeamSerializer

    def get_queryset(self):
        p = get_object_or_404(models.Project, pk=self.kwargs['pk'])
        if not self.request.user.can_access(models.Project, 'read', p):
            raise PermissionDenied()
        project_ct = ContentType.objects.get_for_model(models.Project)
        team_ct = ContentType.objects.get_for_model(self.model)
        all_roles = models.Role.objects.filter(Q(descendents__content_type=project_ct) & Q(descendents__object_id=p.pk), content_type=team_ct)
        return self.model.accessible_objects(self.request.user, 'read_role').filter(pk__in=[t.content_object.pk for t in all_roles])


class ProjectSchedulesList(SubListCreateAPIView):

    view_name = _("Project Schedules")

    model = models.Schedule
    serializer_class = serializers.ScheduleSerializer
    parent_model = models.Project
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class ProjectScmInventorySources(SubListAPIView):

    view_name = _("Project SCM Inventory Sources")
    model = models.InventorySource
    serializer_class = serializers.InventorySourceSerializer
    parent_model = models.Project
    relationship = 'scm_inventory_sources'
    parent_key = 'source_project'


class ProjectActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.Project
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

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.Project
    relationship = 'notification_templates_any'


class ProjectNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.Project
    relationship = 'notification_templates_error'


class ProjectNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.Project
    relationship = 'notification_templates_success'


class ProjectUpdatesList(SubListAPIView):

    model = models.ProjectUpdate
    serializer_class = serializers.ProjectUpdateListSerializer
    parent_model = models.Project
    relationship = 'project_updates'


class ProjectUpdateView(RetrieveAPIView):

    model = models.Project
    serializer_class = serializers.ProjectUpdateViewSerializer
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
                data.update(
                    serializers.ProjectUpdateSerializer(project_update, context=self.get_serializer_context()).to_representation(project_update)
                )
                headers = {'Location': project_update.get_absolute_url(request=request)}
                return Response(data,
                                headers=headers,
                                status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class ProjectUpdateList(ListAPIView):

    model = models.ProjectUpdate
    serializer_class = serializers.ProjectUpdateListSerializer


class ProjectUpdateDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = models.ProjectUpdate
    serializer_class = serializers.ProjectUpdateDetailSerializer


class ProjectUpdateEventsList(SubListAPIView):

    model = models.ProjectUpdateEvent
    serializer_class = serializers.ProjectUpdateEventSerializer
    parent_model = models.ProjectUpdate
    relationship = 'project_update_events'
    view_name = _('Project Update Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(ProjectUpdateEventsList, self).finalize_response(request, response, *args, **kwargs)


class SystemJobEventsList(SubListAPIView):

    model = models.SystemJobEvent
    serializer_class = serializers.SystemJobEventSerializer
    parent_model = models.SystemJob
    relationship = 'system_job_events'
    view_name = _('System Job Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(SystemJobEventsList, self).finalize_response(request, response, *args, **kwargs)




class ProjectUpdateCancel(RetrieveAPIView):

    model = models.ProjectUpdate
    obj_permission_type = 'cancel'
    serializer_class = serializers.ProjectUpdateCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class ProjectUpdateNotificationsList(SubListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    parent_model = models.ProjectUpdate
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class ProjectUpdateScmInventoryUpdates(SubListAPIView):

    view_name = _("Project Update SCM Inventory Updates")
    model = models.InventoryUpdate
    serializer_class = serializers.InventoryUpdateListSerializer
    parent_model = models.ProjectUpdate
    relationship = 'scm_inventory_updates'
    parent_key = 'source_project_update'


class ProjectAccessList(ResourceAccessList):

    model = models.User # needs to be User for AccessLists's
    parent_model = models.Project


class ProjectObjectRolesList(SubListAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer
    parent_model = models.Project
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return models.Role.objects.filter(content_type=content_type, object_id=po.pk)


class ProjectCopy(CopyAPIView):

    model = models.Project
    copy_return_serializer_class = serializers.ProjectSerializer


class UserList(ListCreateAPIView):

    model = models.User
    serializer_class = serializers.UserSerializer
    permission_classes = (UserPermission,)

    def post(self, request, *args, **kwargs):
        ret = super(UserList, self).post( request, *args, **kwargs)
        try:
            if request.data.get('is_system_auditor', False):
                # This is a faux-field that just maps to checking the system
                # auditor role member list.. unfortunately this means we can't
                # set it on creation, and thus needs to be set here.
                user = models.User.objects.get(id=ret.data['id'])
                user.is_system_auditor = request.data['is_system_auditor']
                ret.data['is_system_auditor'] = request.data['is_system_auditor']
        except AttributeError as exc:
            print(exc)
            pass
        return ret


class UserMeList(ListAPIView):

    model = models.User
    serializer_class = serializers.UserSerializer
    view_name = _('Me')

    def get_queryset(self):
        return self.model.objects.filter(pk=self.request.user.pk)


class OAuth2ApplicationList(ListCreateAPIView):

    view_name = _("OAuth 2 Applications")

    model = models.OAuth2Application
    serializer_class = serializers.OAuth2ApplicationSerializer
    swagger_topic = 'Authentication'


class OAuth2ApplicationDetail(RetrieveUpdateDestroyAPIView):

    view_name = _("OAuth 2 Application Detail")

    model = models.OAuth2Application
    serializer_class = serializers.OAuth2ApplicationSerializer
    swagger_topic = 'Authentication'

    def update_raw_data(self, data):
        data.pop('client_secret', None)
        return super(OAuth2ApplicationDetail, self).update_raw_data(data)


class ApplicationOAuth2TokenList(SubListCreateAPIView):

    view_name = _("OAuth 2 Application Tokens")

    model = models.OAuth2AccessToken
    serializer_class = serializers.OAuth2TokenSerializer
    parent_model = models.OAuth2Application
    relationship = 'oauth2accesstoken_set'
    parent_key = 'application'
    swagger_topic = 'Authentication'


class OAuth2ApplicationActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.OAuth2Application
    relationship = 'activitystream_set'
    swagger_topic = 'Authentication'
    search_fields = ('changes',)


class OAuth2TokenList(ListCreateAPIView):

    view_name = _("OAuth2 Tokens")

    model = models.OAuth2AccessToken
    serializer_class = serializers.OAuth2TokenSerializer
    swagger_topic = 'Authentication'


class OAuth2UserTokenList(SubListCreateAPIView):

    view_name = _("OAuth2 User Tokens")

    model = models.OAuth2AccessToken
    serializer_class = serializers.OAuth2TokenSerializer
    parent_model = models.User
    relationship = 'main_oauth2accesstoken'
    parent_key = 'user'
    swagger_topic = 'Authentication'


class UserAuthorizedTokenList(SubListCreateAPIView):

    view_name = _("OAuth2 User Authorized Access Tokens")

    model = models.OAuth2AccessToken
    serializer_class = serializers.UserAuthorizedTokenSerializer
    parent_model = models.User
    relationship = 'oauth2accesstoken_set'
    parent_key = 'user'
    swagger_topic = 'Authentication'

    def get_queryset(self):
        return get_access_token_model().objects.filter(application__isnull=False, user=self.request.user)


class OrganizationApplicationList(SubListCreateAPIView):

    view_name = _("Organization OAuth2 Applications")

    model = models.OAuth2Application
    serializer_class = serializers.OAuth2ApplicationSerializer
    parent_model = models.Organization
    relationship = 'applications'
    parent_key = 'organization'
    swagger_topic = 'Authentication'


class UserPersonalTokenList(SubListCreateAPIView):

    view_name = _("OAuth2 Personal Access Tokens")

    model = models.OAuth2AccessToken
    serializer_class = serializers.UserPersonalTokenSerializer
    parent_model = models.User
    relationship = 'main_oauth2accesstoken'
    parent_key = 'user'
    swagger_topic = 'Authentication'

    def get_queryset(self):
        return get_access_token_model().objects.filter(application__isnull=True, user=self.request.user)


class OAuth2TokenDetail(RetrieveUpdateDestroyAPIView):

    view_name = _("OAuth Token Detail")

    model = models.OAuth2AccessToken
    serializer_class = serializers.OAuth2TokenDetailSerializer
    swagger_topic = 'Authentication'


class OAuth2TokenActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.OAuth2AccessToken
    relationship = 'activitystream_set'
    swagger_topic = 'Authentication'
    search_fields = ('changes',)


class UserTeamsList(SubListAPIView):

    model = models.Team
    serializer_class = serializers.TeamSerializer
    parent_model = models.User

    def get_queryset(self):
        u = get_object_or_404(models.User, pk=self.kwargs['pk'])
        if not self.request.user.can_access(models.User, 'read', u):
            raise PermissionDenied()
        return models.Team.accessible_objects(self.request.user, 'read_role').filter(
            Q(member_role__members=u) | Q(admin_role__members=u)).distinct()


class UserRolesList(SubListAttachDetachAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializerWithParentAccess
    metadata_class = RoleMetadata
    parent_model = models.User
    relationship='roles'
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        u = get_object_or_404(models.User, pk=self.kwargs['pk'])
        if not self.request.user.can_access(models.User, 'read', u):
            raise PermissionDenied()
        content_type = ContentType.objects.get_for_model(models.User)

        return models.Role.filter_visible_roles(
            self.request.user, u.roles.all()
        ).exclude(content_type=content_type, object_id=u.id)

    def post(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if not sub_id:
            return super(UserRolesList, self).post(request)

        user = get_object_or_400(models.User, pk=self.kwargs['pk'])
        role = get_object_or_400(models.Role, pk=sub_id)

        credential_content_type = ContentType.objects.get_for_model(models.Credential)
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

    model = models.Project
    serializer_class = serializers.ProjectSerializer
    parent_model = models.User

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        my_qs = models.Project.accessible_objects(self.request.user, 'read_role')
        user_qs = models.Project.accessible_objects(parent, 'read_role')
        return my_qs & user_qs


class UserOrganizationsList(OrganizationCountsMixin, SubListAPIView):

    model = models.Organization
    serializer_class = serializers.OrganizationSerializer
    parent_model = models.User
    relationship = 'organizations'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        my_qs = models.Organization.accessible_objects(self.request.user, 'read_role')
        user_qs = models.Organization.objects.filter(member_role__members=parent)
        return my_qs & user_qs


class UserAdminOfOrganizationsList(OrganizationCountsMixin, SubListAPIView):

    model = models.Organization
    serializer_class = serializers.OrganizationSerializer
    parent_model = models.User
    relationship = 'admin_of_organizations'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        my_qs = models.Organization.accessible_objects(self.request.user, 'read_role')
        user_qs = models.Organization.objects.filter(admin_role__members=parent)
        return my_qs & user_qs


class UserActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.User
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(actor=parent) | Q(user__in=[parent]))


class UserDetail(RetrieveUpdateDestroyAPIView):

    model = models.User
    serializer_class = serializers.UserSerializer

    def update_filter(self, request, *args, **kwargs):
        ''' make sure non-read-only fields that can only be edited by admins, are only edited by admins '''
        obj = self.get_object()
        can_change = request.user.can_access(models.User, 'change', obj, request.data)
        can_admin = request.user.can_access(models.User, 'admin', obj, request.data)

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
        can_delete = request.user.can_access(models.User, 'delete', obj)
        if not can_delete:
            raise PermissionDenied(_('Cannot delete user.'))
        return super(UserDetail, self).destroy(request, *args, **kwargs)


class UserAccessList(ResourceAccessList):

    model = models.User # needs to be User for AccessLists's
    parent_model = models.User


class CredentialTypeList(ListCreateAPIView):

    model = models.CredentialType
    serializer_class = serializers.CredentialTypeSerializer


class CredentialTypeDetail(RetrieveUpdateDestroyAPIView):

    model = models.CredentialType
    serializer_class = serializers.CredentialTypeSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.managed_by_tower:
            raise PermissionDenied(detail=_("Deletion not allowed for managed credential types"))
        if instance.credentials.exists():
            raise PermissionDenied(detail=_("Credential types that are in use cannot be deleted"))
        return super(CredentialTypeDetail, self).destroy(request, *args, **kwargs)


class CredentialTypeCredentialList(SubListCreateAPIView):

    model = models.Credential
    parent_model = models.CredentialType
    relationship = 'credentials'
    serializer_class = serializers.CredentialSerializer


class CredentialTypeActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.CredentialType
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

    model = models.Credential
    serializer_class = serializers.CredentialSerializerCreate
    filter_backends = ListCreateAPIView.filter_backends + [V1CredentialFilterBackend]


class CredentialOwnerUsersList(SubListAPIView):

    model = models.User
    serializer_class = serializers.UserSerializer
    parent_model = models.Credential
    relationship = 'admin_role.members'


class CredentialOwnerTeamsList(SubListAPIView):

    model = models.Team
    serializer_class = serializers.TeamSerializer
    parent_model = models.Credential

    def get_queryset(self):
        credential = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        if not self.request.user.can_access(models.Credential, 'read', credential):
            raise PermissionDenied()

        content_type = ContentType.objects.get_for_model(self.model)
        teams = [c.content_object.pk for c in credential.admin_role.parents.filter(content_type=content_type)]

        return self.model.objects.filter(pk__in=teams)


class UserCredentialsList(CredentialViewMixin, SubListCreateAPIView):

    model = models.Credential
    serializer_class = serializers.UserCredentialSerializerCreate
    parent_model = models.User
    parent_key = 'user'
    filter_backends = SubListCreateAPIView.filter_backends + [V1CredentialFilterBackend]

    def get_queryset(self):
        user = self.get_parent_object()
        self.check_parent_access(user)

        visible_creds = models.Credential.accessible_objects(self.request.user, 'read_role')
        user_creds = models.Credential.accessible_objects(user, 'read_role')
        return user_creds & visible_creds


class TeamCredentialsList(CredentialViewMixin, SubListCreateAPIView):

    model = models.Credential
    serializer_class = serializers.TeamCredentialSerializerCreate
    parent_model = models.Team
    parent_key = 'team'
    filter_backends = SubListCreateAPIView.filter_backends + [V1CredentialFilterBackend]

    def get_queryset(self):
        team = self.get_parent_object()
        self.check_parent_access(team)

        visible_creds = models.Credential.accessible_objects(self.request.user, 'read_role')
        team_creds = models.Credential.objects.filter(Q(use_role__parents=team.member_role) | Q(admin_role__parents=team.member_role))
        return (team_creds & visible_creds).distinct()


class OrganizationCredentialList(CredentialViewMixin, SubListCreateAPIView):

    model = models.Credential
    serializer_class = serializers.OrganizationCredentialSerializerCreate
    parent_model = models.Organization
    parent_key = 'organization'
    filter_backends = SubListCreateAPIView.filter_backends + [V1CredentialFilterBackend]

    def get_queryset(self):
        organization = self.get_parent_object()
        self.check_parent_access(organization)

        user_visible = models.Credential.accessible_objects(self.request.user, 'read_role').all()
        org_set = models.Credential.accessible_objects(organization.admin_role, 'read_role').all()

        if self.request.user.is_superuser or self.request.user.is_system_auditor:
            return org_set

        return org_set & user_visible


class CredentialDetail(RetrieveUpdateDestroyAPIView):

    model = models.Credential
    serializer_class = serializers.CredentialSerializer
    filter_backends = RetrieveUpdateDestroyAPIView.filter_backends + [V1CredentialFilterBackend]


class CredentialActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.Credential
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class CredentialAccessList(ResourceAccessList):

    model = models.User # needs to be User for AccessLists's
    parent_model = models.Credential


class CredentialObjectRolesList(SubListAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer
    parent_model = models.Credential
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return models.Role.objects.filter(content_type=content_type, object_id=po.pk)


class CredentialCopy(CopyAPIView):

    model = models.Credential
    copy_return_serializer_class = serializers.CredentialSerializer


class CredentialInputSourceDetail(RetrieveUpdateDestroyAPIView):

    view_name = _("Credential Input Source Detail")

    model = models.CredentialInputSource
    serializer_class = serializers.CredentialInputSourceSerializer


class CredentialInputSourceList(ListAPIView):

    view_name = _("Credential Input Sources")

    model = models.CredentialInputSource
    serializer_class = serializers.CredentialInputSourceSerializer


class CredentialInputSourceSubList(SubListCreateAttachDetachAPIView):

    view_name = _("Credential Input Sources")

    model = models.CredentialInputSource
    serializer_class = serializers.CredentialInputSourceSerializer
    parent_model = models.Credential
    relationship = 'input_source'
    parent_key = 'target_credential'


class HostRelatedSearchMixin(object):

    @property
    def related_search_fields(self):
        # Edge-case handle: https://github.com/ansible/ansible-tower/issues/7712
        ret = super(HostRelatedSearchMixin, self).related_search_fields
        ret.append('ansible_facts')
        return ret


class HostList(HostRelatedSearchMixin, ListCreateAPIView):

    always_allow_superuser = False
    model = models.Host
    serializer_class = serializers.HostSerializer

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
            return Response(dict(error=_(str(e))), status=status.HTTP_400_BAD_REQUEST)


class HostDetail(RelatedJobsPreventDeleteMixin, ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    always_allow_superuser = False
    model = models.Host
    serializer_class = serializers.HostSerializer

    def delete(self, request, *args, **kwargs):
        if self.get_object().inventory.pending_deletion:
            return Response({"error": _("The inventory for this host is already being deleted.")},
                            status=status.HTTP_400_BAD_REQUEST)
        return super(HostDetail, self).delete(request, *args, **kwargs)


class HostAnsibleFactsDetail(RetrieveAPIView):

    model = models.Host
    serializer_class = serializers.AnsibleFactsSerializer


class InventoryHostsList(HostRelatedSearchMixin, SubListCreateAttachDetachAPIView):

    model = models.Host
    serializer_class = serializers.HostSerializer
    parent_model = models.Inventory
    relationship = 'hosts'
    parent_key = 'inventory'

    def get_queryset(self):
        inventory = self.get_parent_object()
        return getattrd(inventory, self.relationship).all()


class HostGroupsList(ControlledByScmMixin, SubListCreateAttachDetachAPIView):
    ''' the list of groups a host is directly a member of '''

    model = models.Group
    serializer_class = serializers.GroupSerializer
    parent_model = models.Host
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

    model = models.Group
    serializer_class = serializers.GroupSerializer
    parent_model = models.Host
    relationship = 'groups'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct()
        sublist_qs = parent.all_groups.distinct()
        return qs & sublist_qs


class HostInventorySourcesList(SubListAPIView):

    model = models.InventorySource
    serializer_class = serializers.InventorySourceSerializer
    parent_model = models.Host
    relationship = 'inventory_sources'


class HostSmartInventoriesList(SubListAPIView):
    model = models.Inventory
    serializer_class = serializers.InventorySerializer
    parent_model = models.Host
    relationship = 'smart_inventories'


class HostActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.Host
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(host=parent) | Q(inventory=parent.inventory))


class HostFactVersionsList(SystemTrackingEnforcementMixin, ParentMixin, ListAPIView):

    model = models.Fact
    serializer_class = serializers.FactVersionSerializer
    parent_model = models.Host
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

        return models.Fact.get_timeline(host_obj.id, module=module_spec, ts_from=from_spec, ts_to=to_spec)

    def list(self, *args, **kwargs):
        queryset = self.get_queryset() or []
        return Response(dict(results=self.serializer_class(queryset, many=True).data))


class HostFactCompareView(SystemTrackingEnforcementMixin, SubDetailAPIView):

    model = models.Fact
    parent_model = models.Host
    serializer_class = serializers.FactSerializer
    deprecated = True

    def retrieve(self, request, *args, **kwargs):
        datetime_spec = request.query_params.get('datetime', None)
        module_spec = request.query_params.get('module', "ansible")
        datetime_actual = dateutil.parser.parse(datetime_spec) if datetime_spec is not None else now()

        host_obj = self.get_parent_object()

        fact_entry = models.Fact.get_host_fact(host_obj.id, module_spec, datetime_actual)
        if not fact_entry:
            return Response({'detail': _('Fact not found.')}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(instance=fact_entry).data)


class HostInsights(GenericAPIView):

    model = models.Host
    serializer_class = serializers.EmptySerializer

    def _extract_insights_creds(self, credential):
        return (credential.get_input('username', default=''), credential.get_input('password', default=''))

    def _get_insights(self, url, username, password):
        session = requests.Session()
        session.auth = requests.auth.HTTPBasicAuth(username, password)
        license = get_license(show_key=False).get('license_type', 'UNLICENSED')
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': '{} {} ({})'.format(
                'AWX' if license == 'open' else 'Red Hat Ansible Tower',
                get_awx_version(),
                license
            )
        }
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

    model = models.Group
    serializer_class = serializers.GroupSerializer


class EnforceParentRelationshipMixin(object):
    '''
    Useful when you have a self-refering ManyToManyRelationship.
    * Tower uses a shallow (2-deep only) url pattern. For example:

    When an object hangs off of a parent object you would have the url of the
    form /api/v1/parent_model/34/child_model. If you then wanted a child of the
    child model you would NOT do /api/v1/parent_model/34/child_model/87/child_child_model
    Instead, you would access the child_child_model via /api/v1/child_child_model/87/
    and you would create child_child_model's off of /api/v1/child_model/87/child_child_model_set
    Now, when creating child_child_model related to child_model you still want to
    link child_child_model to parent_model. That's what this class is for
    '''
    enforce_parent_relationship = ''

    def update_raw_data(self, data):
        data.pop(self.enforce_parent_relationship, None)
        return super(EnforceParentRelationshipMixin, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject parent group inventory ID into new group data.
        data = request.data
        # HACK: Make request data mutable.
        if getattr(data, '_mutable', None) is False:
            data._mutable = True
        data[self.enforce_parent_relationship] = getattr(self.get_parent_object(), '%s_id' % self.enforce_parent_relationship)
        return super(EnforceParentRelationshipMixin, self).create(request, *args, **kwargs)


class GroupChildrenList(ControlledByScmMixin, EnforceParentRelationshipMixin, SubListCreateAttachDetachAPIView):

    model = models.Group
    serializer_class = serializers.GroupSerializer
    parent_model = models.Group
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

    model = models.Group
    serializer_class = serializers.GroupSerializer
    parent_model = models.Group

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

    model = models.Host
    serializer_class = serializers.HostSerializer
    parent_model = models.Group
    relationship = 'hosts'

    def update_raw_data(self, data):
        data.pop('inventory', None)
        return super(GroupHostsList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        parent_group = models.Group.objects.get(id=self.kwargs['pk'])
        # Inject parent group inventory ID into new host data.
        request.data['inventory'] = parent_group.inventory_id
        existing_hosts = models.Host.objects.filter(inventory=parent_group.inventory, name=request.data.get('name', ''))
        if existing_hosts.count() > 0 and ('variables' not in request.data or
                                           request.data['variables'] == '' or
                                           request.data['variables'] == '{}' or
                                           request.data['variables'] == '---'):
            request.data['id'] = existing_hosts[0].id
            return self.attach(request, *args, **kwargs)
        return super(GroupHostsList, self).create(request, *args, **kwargs)


class GroupAllHostsList(HostRelatedSearchMixin, SubListAPIView):
    ''' the list of all hosts below a group, even including subgroups '''

    model = models.Host
    serializer_class = serializers.HostSerializer
    parent_model = models.Group
    relationship = 'hosts'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct() # need distinct for '&' operator
        sublist_qs = parent.all_hosts.distinct()
        return qs & sublist_qs


class GroupInventorySourcesList(SubListAPIView):

    model = models.InventorySource
    serializer_class = serializers.InventorySourceSerializer
    parent_model = models.Group
    relationship = 'inventory_sources'


class GroupActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.Group
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(group=parent) | Q(host__in=parent.hosts.all()))


class GroupDetail(RelatedJobsPreventDeleteMixin, ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    model = models.Group
    serializer_class = serializers.GroupSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        if get_request_version(request) == 1:  # TODO: deletion of automatic inventory_source, remove in 3.3
            try:
                obj.deprecated_inventory_source.delete()
            except models.Group.deprecated_inventory_source.RelatedObjectDoesNotExist:
                pass
        obj.delete_recursive()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InventoryGroupsList(SubListCreateAttachDetachAPIView):

    model = models.Group
    serializer_class = serializers.GroupSerializer
    parent_model = models.Inventory
    relationship = 'groups'
    parent_key = 'inventory'


class InventoryRootGroupsList(SubListCreateAttachDetachAPIView):

    model = models.Group
    serializer_class = serializers.GroupSerializer
    parent_model = models.Inventory
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

    model = models.Inventory
    serializer_class = serializers.InventoryVariableDataSerializer


class HostVariableData(BaseVariableData):

    model = models.Host
    serializer_class = serializers.HostVariableDataSerializer


class GroupVariableData(BaseVariableData):

    model = models.Group
    serializer_class = serializers.GroupVariableDataSerializer


class InventoryScriptView(RetrieveAPIView):

    model = models.Inventory
    serializer_class = serializers.InventoryScriptSerializer
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
            if not isinstance(subset, str):
                raise ParseError(_('Inventory subset argument must be a string.'))
            if subset.startswith('slice'):
                slice_number, slice_count = models.Inventory.parse_slice_params(subset)
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

    model = models.Inventory
    serializer_class = serializers.GroupTreeSerializer
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
        all_group_data = serializers.GroupSerializer(groups_qs, many=True).data
        all_group_data_map = dict((x['id'], x) for x in all_group_data)
        tree_data = [all_group_data_map[x] for x in root_group_pks]
        for group_data in tree_data:
            self._populate_group_children(group_data, all_group_data_map,
                                          group_children_map)
        return Response(tree_data)


class InventoryInventorySourcesList(SubListCreateAPIView):

    view_name = _('Inventory Source List')

    model = models.InventorySource
    serializer_class = serializers.InventorySourceSerializer
    parent_model = models.Inventory
    # Sometimes creation blocked by SCM inventory source restrictions
    always_allow_superuser = False
    relationship = 'inventory_sources'
    parent_key = 'inventory'


class InventoryInventorySourcesUpdate(RetrieveAPIView):
    view_name = _('Inventory Sources Update')

    model = models.Inventory
    obj_permission_type = 'start'
    serializer_class = serializers.InventorySourceUpdateSerializer
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
                details.update(serializers.InventoryUpdateDetailSerializer(update, context=self.get_serializer_context()).to_representation(update))
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

    model = models.InventorySource
    serializer_class = serializers.InventorySourceSerializer
    always_allow_superuser = False

    @property
    def allowed_methods(self):
        methods = super(InventorySourceList, self).allowed_methods
        if get_request_version(getattr(self, 'request', None)) == 1:
            methods.remove('POST')
        return methods


class InventorySourceDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):

    model = models.InventorySource
    serializer_class = serializers.InventorySourceSerializer


class InventorySourceSchedulesList(SubListCreateAPIView):

    view_name = _("Inventory Source Schedules")

    model = models.Schedule
    serializer_class = serializers.ScheduleSerializer
    parent_model = models.InventorySource
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class InventorySourceActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.InventorySource
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class InventorySourceNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.InventorySource
    relationship = 'notification_templates_any'

    def post(self, request, *args, **kwargs):
        parent = self.get_parent_object()
        if parent.source not in models.CLOUD_INVENTORY_SOURCES:
            return Response(dict(msg=_("Notification Templates can only be assigned when source is one of {}.")
                                 .format(models.CLOUD_INVENTORY_SOURCES, parent.source)),
                            status=status.HTTP_400_BAD_REQUEST)
        return super(InventorySourceNotificationTemplatesAnyList, self).post(request, *args, **kwargs)


class InventorySourceNotificationTemplatesErrorList(InventorySourceNotificationTemplatesAnyList):

    relationship = 'notification_templates_error'


class InventorySourceNotificationTemplatesSuccessList(InventorySourceNotificationTemplatesAnyList):

    relationship = 'notification_templates_success'


class InventorySourceHostsList(HostRelatedSearchMixin, SubListDestroyAPIView):

    model = models.Host
    serializer_class = serializers.HostSerializer
    parent_model = models.InventorySource
    relationship = 'hosts'
    check_sub_obj_permission = False

    def perform_list_destroy(self, instance_list):
        # Activity stream doesn't record disassociation here anyway
        # no signals-related reason to not bulk-delete
        models.Host.groups.through.objects.filter(
            host__inventory_sources=self.get_parent_object()
        ).delete()
        return super(InventorySourceHostsList, self).perform_list_destroy(instance_list)


class InventorySourceGroupsList(SubListDestroyAPIView):

    model = models.Group
    serializer_class = serializers.GroupSerializer
    parent_model = models.InventorySource
    relationship = 'groups'
    check_sub_obj_permission = False

    def perform_list_destroy(self, instance_list):
        # Same arguments for bulk delete as with host list
        models.Group.hosts.through.objects.filter(
            group__inventory_sources=self.get_parent_object()
        ).delete()
        return super(InventorySourceGroupsList, self).perform_list_destroy(instance_list)


class InventorySourceUpdatesList(SubListAPIView):

    model = models.InventoryUpdate
    serializer_class = serializers.InventoryUpdateListSerializer
    parent_model = models.InventorySource
    relationship = 'inventory_updates'


class InventorySourceCredentialsList(SubListAttachDetachAPIView):

    parent_model = models.InventorySource
    model = models.Credential
    serializer_class = serializers.CredentialSerializer
    relationship = 'credentials'

    def is_valid_relation(self, parent, sub, created=False):
        # Inventory source credentials are exclusive with all other credentials
        # subject to change for https://github.com/ansible/awx/issues/277
        # or https://github.com/ansible/awx/issues/223
        if parent.credentials.exists():
            return {'msg': _("Source already has credential assigned.")}
        error = models.InventorySource.cloud_credential_validation(parent.source, sub)
        if error:
            return {'msg': error}
        return None


class InventorySourceUpdateView(RetrieveAPIView):

    model = models.InventorySource
    obj_permission_type = 'start'
    serializer_class = serializers.InventorySourceUpdateSerializer

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
                data.update(serializers.InventoryUpdateDetailSerializer(update, context=self.get_serializer_context()).to_representation(update))
                return Response(data, status=status.HTTP_202_ACCEPTED, headers=headers)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class InventoryUpdateList(ListAPIView):

    model = models.InventoryUpdate
    serializer_class = serializers.InventoryUpdateListSerializer


class InventoryUpdateDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = models.InventoryUpdate
    serializer_class = serializers.InventoryUpdateDetailSerializer


class InventoryUpdateCredentialsList(SubListAPIView):

    parent_model = models.InventoryUpdate
    model = models.Credential
    serializer_class = serializers.CredentialSerializer
    relationship = 'credentials'


class InventoryUpdateCancel(RetrieveAPIView):

    model = models.InventoryUpdate
    obj_permission_type = 'cancel'
    serializer_class = serializers.InventoryUpdateCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class InventoryUpdateNotificationsList(SubListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    parent_model = models.InventoryUpdate
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class JobTemplateList(ListCreateAPIView):

    model = models.JobTemplate
    metadata_class = JobTypeMetadata
    serializer_class = serializers.JobTemplateSerializer
    always_allow_superuser = False

    def post(self, request, *args, **kwargs):
        ret = super(JobTemplateList, self).post(request, *args, **kwargs)
        if ret.status_code == 201:
            job_template = models.JobTemplate.objects.get(id=ret.data['id'])
            job_template.admin_role.members.add(request.user)
        return ret


class JobTemplateDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):

    model = models.JobTemplate
    metadata_class = JobTypeMetadata
    serializer_class = serializers.JobTemplateSerializer
    always_allow_superuser = False


class JobTemplateLaunch(RetrieveAPIView):

    model = models.JobTemplate
    obj_permission_type = 'start'
    metadata_class = JobTypeMetadata
    serializer_class = serializers.JobLaunchSerializer
    always_allow_superuser = False

    def update_raw_data(self, data):
        try:
            obj = self.get_object()
        except PermissionDenied:
            return data
        extra_vars = data.pop('extra_vars', None) or {}
        if obj:
            needed_passwords = obj.passwords_needed_to_start
            if needed_passwords:
                data['credential_passwords'] = {}
                for p in needed_passwords:
                    data['credential_passwords'][p] = u''
            else:
                data.pop('credential_passwords')
            for v in obj.variables_needed_to_start:
                extra_vars.setdefault(v, u'')
            if extra_vars:
                data['extra_vars'] = extra_vars
            modified_ask_mapping = models.JobTemplate.get_ask_mapping()
            modified_ask_mapping.pop('extra_vars')
            for field, ask_field_name in modified_ask_mapping.items():
                if not getattr(obj, ask_field_name):
                    data.pop(field, None)
                elif field == 'inventory':
                    data[field] = getattrd(obj, "%s.%s" % (field, 'id'), None)
                elif field == 'credentials':
                    data[field] = [cred.id for cred in obj.credentials.all()]
                else:
                    data[field] = getattr(obj, field)
        return data

    def modernize_launch_payload(self, data, obj):
        '''
        Steps to do simple translations of request data to support
        old field structure to launch endpoint
        TODO: delete this method with future API version changes
        '''
        ignored_fields = {}
        modern_data = data.copy()

        for fd in ('credential', 'vault_credential', 'inventory'):
            id_fd = '{}_id'.format(fd)
            if fd not in modern_data and id_fd in modern_data:
                modern_data[fd] = modern_data[id_fd]

        # This block causes `extra_credentials` to _always_ raise error if
        # the launch endpoint if we're accessing `/api/v1/`
        if get_request_version(self.request) == 1 and 'extra_credentials' in modern_data:
            raise ParseError({"extra_credentials": _(
                "Field is not allowed for use with v1 API."
            )})

        # Automatically convert legacy launch credential arguments into a list of `.credentials`
        if 'credentials' in modern_data and (
            'credential' in modern_data or
            'vault_credential' in modern_data or
            'extra_credentials' in modern_data
        ):
            raise ParseError({"error": _(
                "'credentials' cannot be used in combination with 'credential', 'vault_credential', or 'extra_credentials'."
            )})

        if (
            'credential' in modern_data or
            'vault_credential' in modern_data or
            'extra_credentials' in modern_data
        ):
            # make a list of the current credentials
            existing_credentials = obj.credentials.all()
            template_credentials = list(existing_credentials)  # save copy of existing
            new_credentials = []
            for key, conditional, _type, type_repr in (
                ('credential', lambda cred: cred.credential_type.kind != 'ssh', int, 'pk value'),
                ('vault_credential', lambda cred: cred.credential_type.kind != 'vault', int, 'pk value'),
                ('extra_credentials', lambda cred: cred.credential_type.kind not in ('cloud', 'net'), Iterable, 'a list')
            ):
                if key in modern_data:
                    # if a specific deprecated key is specified, remove all
                    # credentials of _that_ type from the list of current
                    # credentials
                    existing_credentials = filter(conditional, existing_credentials)
                    prompted_value = modern_data.pop(key)

                    # validate type, since these are not covered by a serializer
                    if not isinstance(prompted_value, _type):
                        msg = _(
                            "Incorrect type. Expected {}, received {}."
                        ).format(type_repr, prompted_value.__class__.__name__)
                        raise ParseError({key: [msg], 'credentials': [msg]})

                    # add the deprecated credential specified in the request
                    if not isinstance(prompted_value, Iterable) or isinstance(prompted_value, str):
                        prompted_value = [prompted_value]

                    # If user gave extra_credentials, special case to use exactly
                    # the given list without merging with JT credentials
                    if key == 'extra_credentials' and prompted_value:
                        obj._deprecated_credential_launch = True  # signal to not merge credentials
                    new_credentials.extend(prompted_value)

            # combine the list of "new" and the filtered list of "old"
            new_credentials.extend([cred.pk for cred in existing_credentials])
            if new_credentials:
                # If provided list doesn't contain the pre-existing credentials
                # defined on the template, add them back here
                for cred_obj in template_credentials:
                    if cred_obj.pk not in new_credentials:
                        new_credentials.append(cred_obj.pk)
                modern_data['credentials'] = new_credentials

        # credential passwords were historically provided as top-level attributes
        if 'credential_passwords' not in modern_data:
            modern_data['credential_passwords'] = data.copy()

        return (modern_data, ignored_fields)


    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        try:
            modern_data, ignored_fields = self.modernize_launch_payload(
                data=request.data, obj=obj
            )
        except ParseError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=modern_data, context={'template': obj})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ignored_fields.update(serializer._ignored_fields)

        if not request.user.can_access(models.JobLaunchConfig, 'add', serializer.validated_data, template=obj):
            raise PermissionDenied()

        passwords = serializer.validated_data.pop('credential_passwords', {})
        new_job = obj.create_unified_job(**serializer.validated_data)
        result = new_job.signal_start(**passwords)

        if not result:
            data = dict(passwords_needed_to_start=new_job.passwords_needed_to_start)
            new_job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = OrderedDict()
            if isinstance(new_job, models.WorkflowJob):
                data['workflow_job'] = new_job.id
                data['ignored_fields'] = self.sanitize_for_response(ignored_fields)
                data.update(serializers.WorkflowJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
            else:
                data['job'] = new_job.id
                data['ignored_fields'] = self.sanitize_for_response(ignored_fields)
                data.update(serializers.JobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
            headers = {'Location': new_job.get_absolute_url(request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


    def sanitize_for_response(self, data):
        '''
        Model objects cannot be serialized by DRF,
        this replaces objects with their ids for inclusion in response
        '''

        def display_value(val):
            if hasattr(val, 'id'):
                return val.id
            else:
                return val

        sanitized_data = {}
        for field_name, value in data.items():
            if isinstance(value, (set, list)):
                sanitized_data[field_name] = []
                for sub_value in value:
                    sanitized_data[field_name].append(display_value(sub_value))
            else:
                sanitized_data[field_name] = display_value(value)

        return sanitized_data


class JobTemplateSchedulesList(SubListCreateAPIView):

    view_name = _("Job Template Schedules")

    model = models.Schedule
    serializer_class = serializers.ScheduleSerializer
    parent_model = models.JobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class JobTemplateSurveySpec(GenericAPIView):

    model = models.JobTemplate
    obj_permission_type = 'admin'
    serializer_class = serializers.EmptySerializer

    ALLOWED_TYPES = {
        'text': str,
        'textarea': str,
        'password': str,
        'multiplechoice': str,
        'multiselect': str,
        'integer': int,
        'float': float
    }

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not feature_enabled('surveys'):
            raise LicenseForbids(_('Your license does not allow '
                                   'adding surveys.'))

        return Response(obj.display_survey_spec())

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        # Sanity check: Are surveys available on this license?
        # If not, do not allow them to be used.
        if not feature_enabled('surveys'):
            raise LicenseForbids(_('Your license does not allow '
                                   'adding surveys.'))

        if not request.user.can_access(self.model, 'change', obj, None):
            raise PermissionDenied()
        response = self._validate_spec_data(request.data, obj.survey_spec)
        if response:
            return response
        obj.survey_spec = request.data
        obj.save(update_fields=['survey_spec'])
        return Response()

    @staticmethod
    def _validate_spec_data(new_spec, old_spec):
        schema_errors = {}
        for field, expect_type, type_label in [
                ('name', str, 'string'),
                ('description', str, 'string'),
                ('spec', list, 'list of items')]:
            if field not in new_spec:
                schema_errors['error'] = _("Field '{}' is missing from survey spec.").format(field)
            elif not isinstance(new_spec[field], expect_type):
                schema_errors['error'] = _("Expected {} for field '{}', received {} type.").format(
                    type_label, field, type(new_spec[field]).__name__)

        if isinstance(new_spec.get('spec', None), list) and len(new_spec["spec"]) < 1:
            schema_errors['error'] = _("'spec' doesn't contain any items.")

        if schema_errors:
            return Response(schema_errors, status=status.HTTP_400_BAD_REQUEST)

        variable_set = set()
        old_spec_dict = models.JobTemplate.pivot_spec(old_spec)
        for idx, survey_item in enumerate(new_spec["spec"]):
            context = dict(
                idx=str(idx),
                survey_item=survey_item
            )
            # General element validation
            if not isinstance(survey_item, dict):
                return Response(dict(error=_("Survey question %s is not a json object.") % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            for field_name in ['type', 'question_name', 'variable', 'required']:
                if field_name not in survey_item:
                    return Response(dict(error=_("'{field_name}' missing from survey question {idx}").format(
                        field_name=field_name, **context
                    )), status=status.HTTP_400_BAD_REQUEST)
                val = survey_item[field_name]
                allow_types = str
                type_label = 'string'
                if field_name == 'required':
                    allow_types = bool
                    type_label = 'boolean'
                if not isinstance(val, allow_types):
                    return Response(dict(error=_("'{field_name}' in survey question {idx} expected to be {type_label}.").format(
                        field_name=field_name, type_label=type_label, **context
                    )))
            if survey_item['variable'] in variable_set:
                return Response(dict(error=_("'variable' '%(item)s' duplicated in survey question %(survey)s.") % {
                    'item': survey_item['variable'], 'survey': str(idx)}), status=status.HTTP_400_BAD_REQUEST)
            else:
                variable_set.add(survey_item['variable'])

            # Type-specific validation
            # validate question type <-> default type
            qtype = survey_item["type"]
            if qtype not in JobTemplateSurveySpec.ALLOWED_TYPES:
                return Response(dict(error=_(
                    "'{survey_item[type]}' in survey question {idx} is not one of '{allowed_types}' allowed question types."
                ).format(
                    allowed_types=', '.join(JobTemplateSurveySpec.ALLOWED_TYPES.keys()), **context
                )))
            if 'default' in survey_item:
                if not isinstance(survey_item['default'], JobTemplateSurveySpec.ALLOWED_TYPES[qtype]):
                    type_label = 'string'
                    if qtype in ['integer', 'float']:
                        type_label = qtype
                    return Response(dict(error=_(
                        "Default value {survey_item[default]} in survey question {idx} expected to be {type_label}."
                    ).format(
                        type_label=type_label, **context
                    )), status=status.HTTP_400_BAD_REQUEST)
            # additional type-specific properties, the UI provides these even
            # if not applicable to the question, TODO: request that they not do this
            for key in ['min', 'max']:
                if key in survey_item:
                    if survey_item[key] is not None and (not isinstance(survey_item[key], int)):
                        return Response(dict(error=_(
                            "The {min_or_max} limit in survey question {idx} expected to be integer."
                        ).format(min_or_max=key, **context)))
            if qtype in ['multiplechoice', 'multiselect'] and 'choices' not in survey_item:
                return Response(dict(error=_(
                    "Survey question {idx} of type {survey_item[type]} must specify choices.".format(**context)
                )))

            # Process encryption substitution
            if ("default" in survey_item and isinstance(survey_item['default'], str) and
                    survey_item['default'].startswith('$encrypted$')):
                # Submission expects the existence of encrypted DB value to replace given default
                if qtype != "password":
                    return Response(dict(error=_(
                        "$encrypted$ is a reserved keyword for password question defaults, "
                        "survey question {idx} is type {survey_item[type]}."
                    ).format(**context)), status=status.HTTP_400_BAD_REQUEST)
                old_element = old_spec_dict.get(survey_item['variable'], {})
                encryptedish_default_exists = False
                if 'default' in old_element:
                    old_default = old_element['default']
                    if isinstance(old_default, str):
                        if old_default.startswith('$encrypted$'):
                            encryptedish_default_exists = True
                        elif old_default == "":  # unencrypted blank string is allowed as DB value as special case
                            encryptedish_default_exists = True
                if not encryptedish_default_exists:
                    return Response(dict(error=_(
                        "$encrypted$ is a reserved keyword, may not be used for new default in position {idx}."
                    ).format(**context)), status=status.HTTP_400_BAD_REQUEST)
                survey_item['default'] = old_element['default']
            elif qtype == "password" and 'default' in survey_item:
                # Submission provides new encrypted default
                survey_item['default'] = encrypt_value(survey_item['default'])

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        obj.survey_spec = {}
        obj.save()
        return Response()


class WorkflowJobTemplateSurveySpec(WorkflowsEnforcementMixin, JobTemplateSurveySpec):

    model = models.WorkflowJobTemplate


class JobTemplateActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.JobTemplate
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class JobTemplateNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.JobTemplate
    relationship = 'notification_templates_any'


class JobTemplateNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.JobTemplate
    relationship = 'notification_templates_error'


class JobTemplateNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.JobTemplate
    relationship = 'notification_templates_success'


class JobTemplateCredentialsList(SubListCreateAttachDetachAPIView):

    model = models.Credential
    serializer_class = serializers.CredentialSerializer
    parent_model = models.JobTemplate
    relationship = 'credentials'

    def get_queryset(self):
        # Return the full list of credentials
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        sublist_qs = getattrd(parent, self.relationship)
        sublist_qs = sublist_qs.prefetch_related(
            'created_by', 'modified_by',
            'admin_role', 'use_role', 'read_role',
            'admin_role__parents', 'admin_role__members')
        return sublist_qs

    def is_valid_relation(self, parent, sub, created=False):
        if sub.unique_hash() in [cred.unique_hash() for cred in parent.credentials.all()]:
            return {"error": _("Cannot assign multiple {credential_type} credentials.").format(
                credential_type=sub.unique_hash(display=True))}
        kind = sub.credential_type.kind
        if kind not in ('ssh', 'vault', 'cloud', 'net'):
            return {'error': _('Cannot assign a Credential of kind `{}`.').format(kind)}

        return super(JobTemplateCredentialsList, self).is_valid_relation(parent, sub, created)


class JobTemplateExtraCredentialsList(JobTemplateCredentialsList):

    deprecated = True

    def get_queryset(self):
        sublist_qs = super(JobTemplateExtraCredentialsList, self).get_queryset()
        sublist_qs = sublist_qs.filter(credential_type__kind__in=['cloud', 'net'])
        return sublist_qs

    def is_valid_relation(self, parent, sub, created=False):
        valid = super(JobTemplateExtraCredentialsList, self).is_valid_relation(parent, sub, created)
        if sub.credential_type.kind not in ('cloud', 'net'):
            return {'error': _('Extra credentials must be network or cloud.')}
        return valid


class JobTemplateLabelList(DeleteLastUnattachLabelMixin, SubListCreateAttachDetachAPIView):

    model = models.Label
    serializer_class = serializers.LabelSerializer
    parent_model = models.JobTemplate
    relationship = 'labels'

    def post(self, request, *args, **kwargs):
        # If a label already exists in the database, attach it instead of erroring out
        # that it already exists
        if 'id' not in request.data and 'name' in request.data and 'organization' in request.data:
            existing = models.Label.objects.filter(name=request.data['name'], organization_id=request.data['organization'])
            if existing.exists():
                existing = existing[0]
                request.data['id'] = existing.id
                del request.data['name']
                del request.data['organization']
        if models.Label.objects.filter(unifiedjobtemplate_labels=self.kwargs['pk']).count() > 100:
            return Response(dict(msg=_('Maximum number of labels for {} reached.'.format(
                self.parent_model._meta.verbose_name_raw))), status=status.HTTP_400_BAD_REQUEST)
        return super(JobTemplateLabelList, self).post(request, *args, **kwargs)


class JobTemplateCallback(GenericAPIView):

    model = models.JobTemplate
    permission_classes = (JobTemplateCallbackPermission,)
    serializer_class = serializers.EmptySerializer
    parser_classes = api_settings.DEFAULT_PARSER_CLASSES + [FormParser]

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(JobTemplateCallback, self).dispatch(*args, **kwargs)

    def find_matching_hosts(self):
        '''
        Find the host(s) in the job template's inventory that match the remote
        host for the current request.
        '''
        # Find the list of remote host names/IPs to check.
        remote_hosts = set()
        for header in settings.REMOTE_HOST_HEADERS:
            for value in self.request.META.get(header, '').split(','):
                value = value.strip()
                if value:
                    remote_hosts.add(value)
        # Add the reverse lookup of IP addresses.
        for rh in list(remote_hosts):
            try:
                result = socket.gethostbyaddr(rh)
            except socket.herror:
                continue
            except socket.gaierror:
                continue
            remote_hosts.add(result[0])
            remote_hosts.update(result[1])
        # Filter out any .arpa results.
        for rh in list(remote_hosts):
            if rh.endswith('.arpa'):
                remote_hosts.remove(rh)
        if not remote_hosts:
            return set()
        # Find the host objects to search for a match.
        obj = self.get_object()
        hosts = obj.inventory.hosts.all()
        # Populate host_mappings
        host_mappings = {}
        for host in hosts:
            host_name = host.get_effective_host_name()
            host_mappings.setdefault(host_name, [])
            host_mappings[host_name].append(host)
        # Try finding direct match
        matches = set()
        for host_name in remote_hosts:
            if host_name in host_mappings:
                matches.update(host_mappings[host_name])
        if len(matches) == 1:
            return matches
        # Try to resolve forward addresses for each host to find matches.
        for host_name in host_mappings:
            try:
                result = socket.getaddrinfo(host_name, None)
                possible_ips = set(x[4][0] for x in result)
                possible_ips.discard(host_name)
                if possible_ips and possible_ips & remote_hosts:
                    matches.update(host_mappings[host_name])
            except socket.gaierror:
                pass
            except UnicodeError:
                pass
        return matches

    def get(self, request, *args, **kwargs):
        job_template = self.get_object()
        matching_hosts = self.find_matching_hosts()
        data = dict(
            host_config_key=job_template.host_config_key,
            matching_hosts=[x.name for x in matching_hosts],
        )
        if settings.DEBUG:
            d = dict([(k,v) for k,v in request.META.items()
                      if k.startswith('HTTP_') or k.startswith('REMOTE_')])
            data['request_meta'] = d
        return Response(data)

    def post(self, request, *args, **kwargs):
        extra_vars = None
        # Be careful here: content_type can look like '<content_type>; charset=blar'
        if request.content_type.startswith("application/json"):
            extra_vars = request.data.get("extra_vars", None)
        # Permission class should have already validated host_config_key.
        job_template = self.get_object()
        # Attempt to find matching hosts based on remote address.
        matching_hosts = self.find_matching_hosts()
        # If the host is not found, update the inventory before trying to
        # match again.
        inventory_sources_already_updated = []
        if len(matching_hosts) != 1:
            inventory_sources = job_template.inventory.inventory_sources.filter( update_on_launch=True)
            inventory_update_pks = set()
            for inventory_source in inventory_sources:
                if inventory_source.needs_update_on_launch:
                    # FIXME: Doesn't check for any existing updates.
                    inventory_update = inventory_source.create_inventory_update(
                        **{'_eager_fields': {'launch_type': 'callback'}}
                    )
                    inventory_update.signal_start()
                    inventory_update_pks.add(inventory_update.pk)
            inventory_update_qs = models.InventoryUpdate.objects.filter(pk__in=inventory_update_pks, status__in=('pending', 'waiting', 'running'))
            # Poll for the inventory updates we've started to complete.
            while inventory_update_qs.count():
                time.sleep(1.0)
                transaction.commit()
            # Ignore failed inventory updates here, only add successful ones
            # to the list to be excluded when running the job.
            for inventory_update in models.InventoryUpdate.objects.filter(pk__in=inventory_update_pks, status='successful'):
                inventory_sources_already_updated.append(inventory_update.inventory_source_id)
            matching_hosts = self.find_matching_hosts()
        # Check matching hosts.
        if not matching_hosts:
            data = dict(msg=_('No matching host could be found!'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        elif len(matching_hosts) > 1:
            data = dict(msg=_('Multiple hosts matched the request!'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            host = list(matching_hosts)[0]
        if not job_template.can_start_without_user_input(callback_extra_vars=extra_vars):
            data = dict(msg=_('Cannot start automatically, user input required!'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        limit = host.name

        # NOTE: We limit this to one job waiting per host per callblack to keep them from stacking crazily
        if models.Job.objects.filter(
            status__in=['pending', 'waiting', 'running'], job_template=job_template, limit=limit
        ).count() > 0:
            data = dict(msg=_('Host callback job already pending.'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Everything is fine; actually create the job.
        kv = {"limit": limit}
        kv.setdefault('_eager_fields', {})['launch_type'] = 'callback'
        if extra_vars is not None and job_template.ask_variables_on_launch:
            extra_vars_redacted, removed = extract_ansible_vars(extra_vars)
            kv['extra_vars'] = extra_vars_redacted
        kv['_prevent_slicing'] = True  # will only run against 1 host, so no point
        with transaction.atomic():
            job = job_template.create_job(**kv)

        # Send a signal to signify that the job should be started.
        result = job.signal_start(inventory_sources_already_updated=inventory_sources_already_updated)
        if not result:
            data = dict(msg=_('Error starting job!'))
            job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Return the location of the new job.
        headers = {'Location': job.get_absolute_url(request=request)}
        return Response(status=status.HTTP_201_CREATED, headers=headers)


class JobTemplateJobsList(SubListCreateAPIView):

    model = models.Job
    serializer_class = serializers.JobListSerializer
    parent_model = models.JobTemplate
    relationship = 'jobs'
    parent_key = 'job_template'

    @property
    def allowed_methods(self):
        methods = super(JobTemplateJobsList, self).allowed_methods
        if get_request_version(getattr(self, 'request', None)) > 1:
            methods.remove('POST')
        return methods


class JobTemplateSliceWorkflowJobsList(SubListCreateAPIView):

    model = models.WorkflowJob
    serializer_class = serializers.WorkflowJobListSerializer
    parent_model = models.JobTemplate
    relationship = 'slice_workflow_jobs'
    parent_key = 'job_template'


class JobTemplateInstanceGroupsList(SubListAttachDetachAPIView):

    model = models.InstanceGroup
    serializer_class = serializers.InstanceGroupSerializer
    parent_model = models.JobTemplate
    relationship = 'instance_groups'


class JobTemplateAccessList(ResourceAccessList):

    model = models.User # needs to be User for AccessLists's
    parent_model = models.JobTemplate


class JobTemplateObjectRolesList(SubListAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer
    parent_model = models.JobTemplate
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return models.Role.objects.filter(content_type=content_type, object_id=po.pk)


class JobTemplateCopy(CopyAPIView):

    model = models.JobTemplate
    copy_return_serializer_class = serializers.JobTemplateSerializer


class WorkflowJobNodeList(WorkflowsEnforcementMixin, ListAPIView):

    model = models.WorkflowJobNode
    serializer_class = serializers.WorkflowJobNodeListSerializer
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)


class WorkflowJobNodeDetail(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = models.WorkflowJobNode
    serializer_class = serializers.WorkflowJobNodeDetailSerializer


class WorkflowJobNodeCredentialsList(SubListAPIView):

    model = models.Credential
    serializer_class = serializers.CredentialSerializer
    parent_model = models.WorkflowJobNode
    relationship = 'credentials'


class WorkflowJobTemplateNodeList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = models.WorkflowJobTemplateNode
    serializer_class = serializers.WorkflowJobTemplateNodeSerializer
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)


class WorkflowJobTemplateNodeDetail(WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = models.WorkflowJobTemplateNode
    serializer_class = serializers.WorkflowJobTemplateNodeDetailSerializer


class WorkflowJobTemplateNodeCredentialsList(LaunchConfigCredentialsBase):

    parent_model = models.WorkflowJobTemplateNode


class WorkflowJobTemplateNodeChildrenBaseList(WorkflowsEnforcementMixin, EnforceParentRelationshipMixin, SubListCreateAttachDetachAPIView):

    model = models.WorkflowJobTemplateNode
    serializer_class = serializers.WorkflowJobTemplateNodeSerializer
    always_allow_superuser = True
    parent_model = models.WorkflowJobTemplateNode
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

        if parent.id == sub.id:
            return {"Error": _("Cycle detected.")}

        '''
        Look for parent->child connection in all relationships except the relationship that is
        attempting to be added; because it's ok to re-add the relationship
        '''
        relationships = ['success_nodes', 'failure_nodes', 'always_nodes']
        relationships.remove(self.relationship)
        qs = functools.reduce(lambda x, y: (x | y),
                              (Q(**{'{}__in'.format(rel): [sub.id]}) for rel in relationships))

        if models.WorkflowJobTemplateNode.objects.filter(Q(pk=parent.id) & qs).exists():
            return {"Error": _("Relationship not allowed.")}

        parent_node_type_relationship = getattr(parent, self.relationship)
        parent_node_type_relationship.add(sub)

        graph = WorkflowDAG(parent.workflow_job_template)
        if graph.has_cycle():
            parent_node_type_relationship.remove(sub)
            return {"Error": _("Cycle detected.")}
        parent_node_type_relationship.remove(sub)
        return None


class WorkflowJobTemplateNodeSuccessNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'success_nodes'


class WorkflowJobTemplateNodeFailureNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'failure_nodes'


class WorkflowJobTemplateNodeAlwaysNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'always_nodes'


class WorkflowJobNodeChildrenBaseList(WorkflowsEnforcementMixin, SubListAPIView):

    model = models.WorkflowJobNode
    serializer_class = serializers.WorkflowJobNodeListSerializer
    parent_model = models.WorkflowJobNode
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

    model = models.WorkflowJobTemplate
    serializer_class = serializers.WorkflowJobTemplateSerializer
    always_allow_superuser = False


class WorkflowJobTemplateDetail(RelatedJobsPreventDeleteMixin, WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = models.WorkflowJobTemplate
    serializer_class = serializers.WorkflowJobTemplateSerializer
    always_allow_superuser = False


class WorkflowJobTemplateCopy(WorkflowsEnforcementMixin, CopyAPIView):

    model = models.WorkflowJobTemplate
    copy_return_serializer_class = serializers.WorkflowJobTemplateSerializer

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
                            logger.debug(
                                'Deep copy: removing {} from relationship due to permissions'.format(cred))
                            item.remove(cred.pk)
            obj.save()


class WorkflowJobTemplateLabelList(WorkflowsEnforcementMixin, JobTemplateLabelList):
    parent_model = models.WorkflowJobTemplate


class WorkflowJobTemplateLaunch(WorkflowsEnforcementMixin, RetrieveAPIView):


    model = models.WorkflowJobTemplate
    obj_permission_type = 'start'
    serializer_class = serializers.WorkflowJobLaunchSerializer
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
            if obj.ask_inventory_on_launch:
                data['inventory'] = obj.inventory_id
            else:
                data.pop('inventory', None)
        return data

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        if 'inventory_id' in request.data:
            request.data['inventory'] = request.data['inventory_id']

        serializer = self.serializer_class(instance=obj, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.can_access(models.JobLaunchConfig, 'add', serializer.validated_data, template=obj):
            raise PermissionDenied()

        new_job = obj.create_unified_job(**serializer.validated_data)
        new_job.signal_start()

        data = OrderedDict()
        data['workflow_job'] = new_job.id
        data['ignored_fields'] = serializer._ignored_fields
        data.update(serializers.WorkflowJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
        headers = {'Location': new_job.get_absolute_url(request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class WorkflowJobRelaunch(WorkflowsEnforcementMixin, GenericAPIView):

    model = models.WorkflowJob
    obj_permission_type = 'start'
    serializer_class = serializers.EmptySerializer

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
        if obj.is_sliced_job:
            jt = obj.job_template
            if not jt:
                raise ParseError(_('Cannot relaunch slice workflow job orphaned from job template.'))
            elif not jt.inventory or min(jt.inventory.hosts.count(), jt.job_slice_count) != obj.workflow_nodes.count():
                raise ParseError(_('Cannot relaunch sliced workflow job after slice count has changed.'))
        new_workflow_job = obj.create_relaunch_workflow_job()
        new_workflow_job.signal_start()

        data = serializers.WorkflowJobSerializer(new_workflow_job, context=self.get_serializer_context()).data
        headers = {'Location': new_workflow_job.get_absolute_url(request=request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class WorkflowJobTemplateWorkflowNodesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    model = models.WorkflowJobTemplateNode
    serializer_class = serializers.WorkflowJobTemplateNodeSerializer
    parent_model = models.WorkflowJobTemplate
    relationship = 'workflow_job_template_nodes'
    parent_key = 'workflow_job_template'
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)

    def get_queryset(self):
        return super(WorkflowJobTemplateWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobTemplateJobsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = models.WorkflowJob
    serializer_class = serializers.WorkflowJobListSerializer
    parent_model = models.WorkflowJobTemplate
    relationship = 'workflow_jobs'
    parent_key = 'workflow_job_template'


class WorkflowJobTemplateSchedulesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    view_name = _("Workflow Job Template Schedules")

    model = models.Schedule
    serializer_class = serializers.ScheduleSerializer
    parent_model = models.WorkflowJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class WorkflowJobTemplateNotificationTemplatesAnyList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.WorkflowJobTemplate
    relationship = 'notification_templates_any'


class WorkflowJobTemplateNotificationTemplatesErrorList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.WorkflowJobTemplate
    relationship = 'notification_templates_error'


class WorkflowJobTemplateNotificationTemplatesSuccessList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.WorkflowJobTemplate
    relationship = 'notification_templates_success'


class WorkflowJobTemplateAccessList(WorkflowsEnforcementMixin, ResourceAccessList):

    model = models.User # needs to be User for AccessLists's
    parent_model = models.WorkflowJobTemplate


class WorkflowJobTemplateObjectRolesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer
    parent_model = models.WorkflowJobTemplate
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return models.Role.objects.filter(content_type=content_type, object_id=po.pk)


class WorkflowJobTemplateActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.WorkflowJobTemplate
    relationship = 'activitystream_set'
    search_fields = ('changes',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(workflow_job_template=parent) |
                         Q(workflow_job_template_node__workflow_job_template=parent)).distinct()


class WorkflowJobList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = models.WorkflowJob
    serializer_class = serializers.WorkflowJobListSerializer


class WorkflowJobDetail(WorkflowsEnforcementMixin, UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = models.WorkflowJob
    serializer_class = serializers.WorkflowJobSerializer


class WorkflowJobWorkflowNodesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = models.WorkflowJobNode
    serializer_class = serializers.WorkflowJobNodeListSerializer
    always_allow_superuser = True
    parent_model = models.WorkflowJob
    relationship = 'workflow_job_nodes'
    parent_key = 'workflow_job'
    search_fields = ('unified_job_template__name', 'unified_job_template__description',)

    def get_queryset(self):
        return super(WorkflowJobWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobCancel(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = models.WorkflowJob
    obj_permission_type = 'cancel'
    serializer_class = serializers.WorkflowJobCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            schedule_task_manager()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class WorkflowJobNotificationsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    parent_model = models.WorkflowJob
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class WorkflowJobActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.WorkflowJob
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class SystemJobTemplateList(ListAPIView):

    model = models.SystemJobTemplate
    serializer_class = serializers.SystemJobTemplateSerializer

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_system_auditor:
            raise PermissionDenied(_("Superuser privileges needed."))
        return super(SystemJobTemplateList, self).get(request, *args, **kwargs)


class SystemJobTemplateDetail(RetrieveAPIView):

    model = models.SystemJobTemplate
    serializer_class = serializers.SystemJobTemplateSerializer


class SystemJobTemplateLaunch(GenericAPIView):

    model = models.SystemJobTemplate
    obj_permission_type = 'start'
    serializer_class = serializers.EmptySerializer

    def get(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        new_job = obj.create_unified_job(extra_vars=request.data.get('extra_vars', {}))
        new_job.signal_start()
        data = OrderedDict()
        data['system_job'] = new_job.id
        data.update(serializers.SystemJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
        headers = {'Location': new_job.get_absolute_url(request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class SystemJobTemplateSchedulesList(SubListCreateAPIView):

    view_name = _("System Job Template Schedules")

    model = models.Schedule
    serializer_class = serializers.ScheduleSerializer
    parent_model = models.SystemJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class SystemJobTemplateJobsList(SubListAPIView):

    model = models.SystemJob
    serializer_class = serializers.SystemJobListSerializer
    parent_model = models.SystemJobTemplate
    relationship = 'jobs'
    parent_key = 'system_job_template'


class SystemJobTemplateNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.SystemJobTemplate
    relationship = 'notification_templates_any'


class SystemJobTemplateNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.SystemJobTemplate
    relationship = 'notification_templates_error'


class SystemJobTemplateNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer
    parent_model = models.SystemJobTemplate
    relationship = 'notification_templates_success'


class JobList(ListCreateAPIView):

    model = models.Job
    metadata_class = JobTypeMetadata
    serializer_class = serializers.JobListSerializer

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

    model = models.Job
    metadata_class = JobTypeMetadata
    serializer_class = serializers.JobDetailSerializer

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

    model = models.Credential
    serializer_class = serializers.CredentialSerializer
    parent_model = models.Job
    relationship = 'credentials'


class JobExtraCredentialsList(JobCredentialsList):

    deprecated = True

    def get_queryset(self):
        sublist_qs = super(JobExtraCredentialsList, self).get_queryset()
        sublist_qs = sublist_qs.filter(credential_type__kind__in=['cloud', 'net'])
        return sublist_qs


class JobLabelList(SubListAPIView):

    model = models.Label
    serializer_class = serializers.LabelSerializer
    parent_model = models.Job
    relationship = 'labels'
    parent_key = 'job'


class WorkflowJobLabelList(WorkflowsEnforcementMixin, JobLabelList):
    parent_model = models.WorkflowJob


class JobActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.Job
    relationship = 'activitystream_set'
    search_fields = ('changes',)


# TODO: remove endpoint in 3.3
class JobStart(GenericAPIView):

    model = models.Job
    obj_permission_type = 'start'
    serializer_class = serializers.EmptySerializer
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

    model = models.Job
    obj_permission_type = 'cancel'
    serializer_class = serializers.JobCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class JobRelaunch(RetrieveAPIView):

    model = models.Job
    obj_permission_type = 'start'
    serializer_class = serializers.JobRelaunchSerializer

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

        new_job = obj.copy_unified_job(**copy_kwargs)
        result = new_job.signal_start(**serializer.validated_data['credential_passwords'])
        if not result:
            data = dict(msg=_('Error starting job!'))
            new_job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = serializers.JobSerializer(new_job, context=context).data
            # Add job key to match what old relaunch returned.
            data['job'] = new_job.id
            headers = {'Location': new_job.get_absolute_url(request=request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class JobCreateSchedule(RetrieveAPIView):

    model = models.Job
    obj_permission_type = 'start'
    serializer_class = serializers.JobCreateScheduleSerializer

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
        existing_names = models.Schedule.objects.filter(name__startswith=name).values_list('name', flat=True)
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
        if not request.user.can_access(models.Schedule, 'add', schedule_data):
            raise PermissionDenied()

        creds_list = schedule_data.pop('credentials')
        schedule = models.Schedule.objects.create(**schedule_data)
        schedule.credentials.add(*creds_list)

        data = serializers.ScheduleSerializer(schedule, context=self.get_serializer_context()).data
        data.serializer.instance = None  # hack to avoid permissions.py assuming this is Job model
        headers = {'Location': schedule.get_absolute_url(request=request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class JobNotificationsList(SubListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    parent_model = models.Job
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class BaseJobHostSummariesList(SubListAPIView):

    model = models.JobHostSummary
    serializer_class = serializers.JobHostSummarySerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_host_summaries'
    view_name = _('Job Host Summaries List')
    search_fields = ('host_name',)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).select_related('job', 'job__job_template', 'host')


class HostJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = models.Host


class GroupJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = models.Group


class JobJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = models.Job


class JobHostSummaryDetail(RetrieveAPIView):

    model = models.JobHostSummary
    serializer_class = serializers.JobHostSummarySerializer


class JobEventList(ListAPIView):

    model = models.JobEvent
    serializer_class = serializers.JobEventSerializer
    search_fields = ('stdout',)


class JobEventDetail(RetrieveAPIView):

    model = models.JobEvent
    serializer_class = serializers.JobEventSerializer


class JobEventChildrenList(SubListAPIView):

    model = models.JobEvent
    serializer_class = serializers.JobEventSerializer
    parent_model = models.JobEvent
    relationship = 'children'
    view_name = _('Job Event Children List')
    search_fields = ('stdout',)


class JobEventHostsList(HostRelatedSearchMixin, SubListAPIView):

    model = models.Host
    serializer_class = serializers.HostSerializer
    parent_model = models.JobEvent
    relationship = 'hosts'
    view_name = _('Job Event Hosts List')


class BaseJobEventsList(SubListAPIView):

    model = models.JobEvent
    serializer_class = serializers.JobEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_events'
    view_name = _('Job Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.MAX_UI_JOB_EVENTS
        return super(BaseJobEventsList, self).finalize_response(request, response, *args, **kwargs)


class HostJobEventsList(BaseJobEventsList):

    parent_model = models.Host

    def get_queryset(self):
        parent_obj = self.get_parent_object()
        self.check_parent_access(parent_obj)
        qs = self.request.user.get_queryset(self.model).filter(
            Q(host=parent_obj) | Q(hosts=parent_obj)).distinct()
        return qs


class GroupJobEventsList(BaseJobEventsList):

    parent_model = models.Group


class JobJobEventsList(BaseJobEventsList):

    parent_model = models.Job

    def get_queryset(self):
        job = self.get_parent_object()
        self.check_parent_access(job)
        qs = job.job_events
        qs = qs.select_related('host')
        qs = qs.prefetch_related('hosts', 'children')
        return qs.all()


class AdHocCommandList(ListCreateAPIView):

    model = models.AdHocCommand
    serializer_class = serializers.AdHocCommandListSerializer
    always_allow_superuser = False

    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(AdHocCommandList, self).dispatch(*args, **kwargs)

    def update_raw_data(self, data):
        # Hide inventory and limit fields from raw data, since they will be set
        # automatically by sub list create view.
        parent_model = getattr(self, 'parent_model', None)
        if parent_model in (models.Host, models.Group):
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
            if isinstance(parent_obj, (models.Host, models.Group)):
                data['inventory'] = parent_obj.inventory_id
                data['limit'] = parent_obj.name

        # Check for passwords needed before creating ad hoc command.
        credential_pk = get_pk_from_dict(request.data, 'credential')
        if credential_pk:
            credential = get_object_or_400(models.Credential, pk=credential_pk)
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

    parent_model = models.Inventory
    relationship = 'ad_hoc_commands'
    parent_key = 'inventory'


class GroupAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = models.Group
    relationship = 'ad_hoc_commands'


class HostAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = models.Host
    relationship = 'ad_hoc_commands'


class AdHocCommandDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = models.AdHocCommand
    serializer_class = serializers.AdHocCommandDetailSerializer


class AdHocCommandCancel(RetrieveAPIView):

    model = models.AdHocCommand
    obj_permission_type = 'cancel'
    serializer_class = serializers.AdHocCommandCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class AdHocCommandRelaunch(GenericAPIView):

    model = models.AdHocCommand
    obj_permission_type = 'start'
    serializer_class = serializers.AdHocCommandRelaunchSerializer

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
        serializer = serializers.AdHocCommandSerializer(data=data, context=self.get_serializer_context())
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
            data = serializers.AdHocCommandSerializer(new_ad_hoc_command, context=self.get_serializer_context()).data
            # Add ad_hoc_command key to match what was previously returned.
            data['ad_hoc_command'] = new_ad_hoc_command.id
            headers = {'Location': new_ad_hoc_command.get_absolute_url(request=request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class AdHocCommandEventList(ListAPIView):

    model = models.AdHocCommandEvent
    serializer_class = serializers.AdHocCommandEventSerializer
    search_fields = ('stdout',)


class AdHocCommandEventDetail(RetrieveAPIView):

    model = models.AdHocCommandEvent
    serializer_class = serializers.AdHocCommandEventSerializer


class BaseAdHocCommandEventsList(SubListAPIView):

    model = models.AdHocCommandEvent
    serializer_class = serializers.AdHocCommandEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'ad_hoc_command_events'
    view_name = _('Ad Hoc Command Events List')
    search_fields = ('stdout',)


class HostAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = models.Host


#class GroupJobEventsList(BaseJobEventsList):
#    parent_model = Group


class AdHocCommandAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = models.AdHocCommand


class AdHocCommandActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    parent_model = models.AdHocCommand
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class AdHocCommandNotificationsList(SubListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    parent_model = models.AdHocCommand
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class SystemJobList(ListCreateAPIView):

    model = models.SystemJob
    serializer_class = serializers.SystemJobListSerializer

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_system_auditor:
            raise PermissionDenied(_("Superuser privileges needed."))
        return super(SystemJobList, self).get(request, *args, **kwargs)


class SystemJobDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = models.SystemJob
    serializer_class = serializers.SystemJobSerializer


class SystemJobCancel(RetrieveAPIView):

    model = models.SystemJob
    obj_permission_type = 'cancel'
    serializer_class = serializers.SystemJobCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class SystemJobNotificationsList(SubListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    parent_model = models.SystemJob
    relationship = 'notifications'
    search_fields = ('subject', 'notification_type', 'body',)


class UnifiedJobTemplateList(ListAPIView):

    model = models.UnifiedJobTemplate
    serializer_class = serializers.UnifiedJobTemplateSerializer


class UnifiedJobList(ListAPIView):

    model = models.UnifiedJob
    serializer_class = serializers.UnifiedJobListSerializer


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
    serializer_class = serializers.UnifiedJobStdoutSerializer
    renderer_classes = [renderers.BrowsableAPIRenderer, StaticHTMLRenderer,
                        renderers.PlainTextRenderer, renderers.AnsiTextRenderer,
                        JSONRenderer, renderers.DownloadTextRenderer,
                        renderers.AnsiDownloadRenderer]
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
                if type(unified_job) == models.ProjectUpdate:
                    redactor.register(UriCleaner.remove_sensitive)
                response = HttpResponse(FileWrapper(redactor), content_type='text/plain')
                response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)
                return response
            else:
                return super(UnifiedJobStdout, self).retrieve(request, *args, **kwargs)
        except models.StdoutMaxBytesExceeded as e:
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

    model = models.ProjectUpdate


class InventoryUpdateStdout(UnifiedJobStdout):

    model = models.InventoryUpdate


class JobStdout(UnifiedJobStdout):

    model = models.Job


class AdHocCommandStdout(UnifiedJobStdout):

    model = models.AdHocCommand


class NotificationTemplateList(ListCreateAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer


class NotificationTemplateDetail(RetrieveUpdateDestroyAPIView):

    model = models.NotificationTemplate
    serializer_class = serializers.NotificationTemplateSerializer

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
    model = models.NotificationTemplate
    obj_permission_type = 'start'
    serializer_class = serializers.EmptySerializer

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
            data.update(serializers.NotificationSerializer(notification, context=self.get_serializer_context()).to_representation(notification))
            headers = {'Location': notification.get_absolute_url(request=request)}
            return Response(data,
                            headers=headers,
                            status=status.HTTP_202_ACCEPTED)


class NotificationTemplateNotificationList(SubListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    parent_model = models.NotificationTemplate
    relationship = 'notifications'
    parent_key = 'notification_template'
    search_fields = ('subject', 'notification_type', 'body',)


class NotificationTemplateCopy(CopyAPIView):

    model = models.NotificationTemplate
    copy_return_serializer_class = serializers.NotificationTemplateSerializer


class NotificationList(ListAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer
    search_fields = ('subject', 'notification_type', 'body',)


class NotificationDetail(RetrieveAPIView):

    model = models.Notification
    serializer_class = serializers.NotificationSerializer


class LabelList(ListCreateAPIView):

    model = models.Label
    serializer_class = serializers.LabelSerializer


class LabelDetail(RetrieveUpdateAPIView):

    model = models.Label
    serializer_class = serializers.LabelSerializer


class ActivityStreamList(ActivityStreamEnforcementMixin, SimpleListAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer
    search_fields = ('changes',)


class ActivityStreamDetail(ActivityStreamEnforcementMixin, RetrieveAPIView):

    model = models.ActivityStream
    serializer_class = serializers.ActivityStreamSerializer


class RoleList(ListAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        result = models.Role.visible_roles(self.request.user)
        # Sanity check: is the requesting user an orphaned non-admin/auditor?
        # if yes, make system admin/auditor mandatorily visible.
        if not self.request.user.organizations.exists() and\
           not self.request.user.is_superuser and\
           not self.request.user.is_system_auditor:
            mandatories = ('system_administrator', 'system_auditor')
            super_qs = models.Role.objects.filter(singleton_name__in=mandatories)
            result = result | super_qs
        return result


class RoleDetail(RetrieveAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer


class RoleUsersList(SubListAttachDetachAPIView):

    model = models.User
    serializer_class = serializers.UserSerializer
    parent_model = models.Role
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

        user = get_object_or_400(models.User, pk=sub_id)
        role = self.get_parent_object()

        credential_content_type = ContentType.objects.get_for_model(models.Credential)
        if role.content_type == credential_content_type:
            if role.content_object.organization and user not in role.content_object.organization.member_role:
                data = dict(msg=_("You cannot grant credential access to a user not in the credentials' organization"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            if not role.content_object.organization and not request.user.is_superuser:
                data = dict(msg=_("You cannot grant private credential access to another user"))
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        return super(RoleUsersList, self).post(request, *args, **kwargs)


class RoleTeamsList(SubListAttachDetachAPIView):

    model = models.Team
    serializer_class = serializers.TeamSerializer
    parent_model = models.Role
    relationship = 'member_role.parents'
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        role = self.get_parent_object()
        self.check_parent_access(role)
        return models.Team.objects.filter(member_role__children=role)

    def post(self, request, pk, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if not sub_id:
            return super(RoleTeamsList, self).post(request)

        team = get_object_or_400(models.Team, pk=sub_id)
        role = models.Role.objects.get(pk=self.kwargs['pk'])

        organization_content_type = ContentType.objects.get_for_model(models.Organization)
        if role.content_type == organization_content_type and role.role_field in ['member_role', 'admin_role']:
            data = dict(msg=_("You cannot assign an Organization participation role as a child role for a Team."))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        credential_content_type = ContentType.objects.get_for_model(models.Credential)
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

    model = models.Role
    serializer_class = serializers.RoleSerializer
    parent_model = models.Role
    relationship = 'parents'
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        role = models.Role.objects.get(pk=self.kwargs['pk'])
        return models.Role.filter_visible_roles(self.request.user, role.parents.all())


class RoleChildrenList(SubListAPIView):

    model = models.Role
    serializer_class = serializers.RoleSerializer
    parent_model = models.Role
    relationship = 'children'
    permission_classes = (IsAuthenticated,)
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        role = models.Role.objects.get(pk=self.kwargs['pk'])
        return models.Role.filter_visible_roles(self.request.user, role.children.all())


# Create view functions for all of the class-based views to simplify inclusion
# in URL patterns and reverse URL lookups, converting CamelCase names to
# lowercase_with_underscore (e.g. MyView.as_view() becomes my_view).
this_module = sys.modules[__name__]
for attr, value in list(locals().items()):
    if isinstance(value, type) and issubclass(value, APIView):
        name = camelcase_to_underscore(attr)
        view = value.as_view()
        setattr(this_module, name, view)
