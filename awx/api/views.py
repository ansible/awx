
# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import datetime
import dateutil
import functools
import time
import re
import socket
import sys

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import FieldError
from django.db.models import Q, Count, Sum
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string

# Django REST Framework
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.pagination import BasePaginationSerializer
from rest_framework.parsers import YAMLParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import YAMLRenderer
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import exception_handler
from rest_framework import status

# Ansi2HTML
from ansi2html import Ansi2HTMLConverter
from ansi2html.style import SCHEME

# QSStats
import qsstats

# AWX
from awx.main.task_engine import TaskSerializer, TASK_FILE
from awx.main.models import *
from awx.main.utils import *
from awx.main.access import get_user_queryset
from awx.main.ha import is_ha_environment
from awx.api.authentication import JobTaskAuthentication
from awx.api.permissions import *
from awx.api.renderers import *
from awx.api.serializers import *
from awx.api.utils.decorators import paginated
from awx.api.generics import *
from awx.api.generics import get_view_name


def api_exception_handler(exc):
    '''
    Override default API exception handler to catch IntegrityError exceptions.
    '''
    if isinstance(exc, IntegrityError):
        exc = ParseError(exc.args[0])
    if isinstance(exc, FieldError):
        exc = ParseError(exc.args[0])
    return exception_handler(exc)


class ApiRootView(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    view_name = 'REST API'

    def get(self, request, format=None):
        ''' list supported API versions '''

        current = reverse('api:api_v1_root_view', args=[])
        data = dict(
           description = 'Ansible Tower REST API',
           current_version = current,
           available_versions = dict(
              v1 = current
           )
        )
        return Response(data)

class ApiV1RootView(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    view_name = 'Version 1'

    def get(self, request, format=None):
        ''' list top level resources '''

        data = SortedDict()
        data['authtoken'] = reverse('api:auth_token_view')
        data['ping'] = reverse('api:api_v1_ping_view')
        data['config'] = reverse('api:api_v1_config_view')
        data['me'] = reverse('api:user_me_list')
        data['dashboard'] = reverse('api:dashboard_view')
        data['organizations'] = reverse('api:organization_list')
        data['users'] = reverse('api:user_list')
        data['projects'] = reverse('api:project_list')
        data['teams'] = reverse('api:team_list')
        data['credentials'] = reverse('api:credential_list')
        data['inventory'] = reverse('api:inventory_list')
        data['inventory_scripts'] = reverse('api:inventory_script_list')
        data['inventory_sources'] = reverse('api:inventory_source_list')
        data['groups'] = reverse('api:group_list')
        data['hosts'] = reverse('api:host_list')
        data['job_templates'] = reverse('api:job_template_list')
        data['jobs'] = reverse('api:job_list')
        data['system_job_templates'] = reverse('api:system_job_template_list')
        data['system_jobs'] = reverse('api:system_job_list')
        data['schedules'] = reverse('api:schedule_list')
        data['unified_job_templates'] = reverse('api:unified_job_template_list')
        data['unified_jobs'] = reverse('api:unified_job_list')
        data['activity_stream'] = reverse('api:activity_stream_list')
        return Response(data)


class ApiV1PingView(APIView):
    """A simple view that reports very basic information about this Tower
    instance, which is acceptable to be public information.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()
    view_name = 'Ping'
    new_in_210 = True

    def get(self, request, format=None):
        """Return some basic information about this Tower instance.

        Everything returned here should be considered public / insecure, as
        this requires no auth and is intended for use by the installer process.
        """
        # Most of this response is canned; just build the dictionary.
        response = {
            'ha': is_ha_environment(),
            'role': Instance.objects.my_role(),
            'version': get_awx_version(),
        }

        # If this is an HA environment, we also include the IP address of
        # all of the instances.
        #
        # Set up a default structure.
        response['instances'] = {
            'primary': None,
            'secondaries': [],
        }

        # Add all of the instances into the structure.
        for instance in Instance.objects.all():
            if instance.primary:
                response['instances']['primary'] = instance.hostname
            else:
                response['instances']['secondaries'].append(instance.hostname)
        response['instances']['secondaries'].sort()

        # Done; return the response.
        return Response(response)


class ApiV1ConfigView(APIView):

    permission_classes = (IsAuthenticated,)
    view_name = 'Configuration'

    def get(self, request, format=None):
        '''Return various sitewide configuration settings.'''

        license_reader = TaskSerializer()
        license_data   = license_reader.from_file(show_key=request.user.is_superuser)

        data = dict(
            time_zone=settings.TIME_ZONE,
            license_info=license_data,
            version=get_awx_version(),
            ansible_version=get_ansible_version(),
            eula=render_to_string("eula.md"),
        )

        # If LDAP is enabled, user_ldap_fields will return a list of field
        # names that are managed by LDAP and should be read-only for users with
        # a non-empty ldap_dn attribute.
        if getattr(settings, 'AUTH_LDAP_SERVER_URI', None):
            user_ldap_fields = ['username', 'password']
            user_ldap_fields.extend(getattr(settings, 'AUTH_LDAP_USER_ATTR_MAP', {}).keys())
            user_ldap_fields.extend(getattr(settings, 'AUTH_LDAP_USER_FLAGS_BY_GROUP', {}).keys())
            data['user_ldap_fields'] = user_ldap_fields

        if request.user.is_superuser or request.user.admin_of_organizations.filter(active=True).count():
            data.update(dict(
                project_base_dir = settings.PROJECTS_ROOT,
                project_local_paths = Project.get_local_path_choices(),
            ))

        return Response(data)

    def post(self, request):
        if not request.user.is_superuser:
            return Response(None, status=status.HTTP_404_NOT_FOUND)
        try:
            data_actual = json.dumps(request.DATA)
        except Exception, e:
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        if "eula_accepted" not in data_actual:
            return Response({"error": "Missing 'eula_accepted' property"}, status=status.HTTP_400_BAD_REQUEST)
        if not data_actual["eula_accepted"]:
            return Response({"error": "'eula_accepted' must be True"}, status=status.HTTP_400_BAD_REQUEST)
        data_actual.pop("eula_accepted")
        license_reader = TaskSerializer()
        try:
            license_data = license_reader.from_string(data_actual)
        except Exception, e:
            return Response({"error": "Invalid License"}, status=status.HTTP_400_BAD_REQUEST)
        if license_data['valid_key']:
            fh = open(TASK_FILE, "w")
            fh.write(data_actual)
            fh.close()
            return Response(license_data)
        return Response({"error": "Invalid license"}, status=status.HTTP_400_BAD_REQUEST)

class DashboardView(APIView):

    view_name = "Dashboard"
    new_in_14 = True

    def get(self, request, format=None):
        ''' Show Dashboard Details '''
        data = SortedDict()
        data['related'] = {'jobs_graph': reverse('api:dashboard_jobs_graph_view'),
                           'inventory_graph': reverse('api:dashboard_inventory_graph_view')}
        user_inventory = get_user_queryset(request.user, Inventory)
        inventory_with_failed_hosts = user_inventory.filter(hosts_with_active_failures__gt=0)
        user_inventory_external = user_inventory.filter(has_inventory_sources=True)
        failed_inventory = sum(i.inventory_sources_with_failures for i in user_inventory)
        data['inventories'] = {'url': reverse('api:inventory_list'),
                               'total': user_inventory.count(),
                               'total_with_inventory_source': user_inventory_external.count(),
                               'job_failed': inventory_with_failed_hosts.count(),
                               'inventory_failed': failed_inventory}
        user_inventory_sources = get_user_queryset(request.user, InventorySource)
        rax_inventory_sources = user_inventory_sources.filter(source='rax')
        rax_inventory_failed = rax_inventory_sources.filter(status='failed')
        ec2_inventory_sources = user_inventory_sources.filter(source='ec2')
        ec2_inventory_failed = ec2_inventory_sources.filter(status='failed')
        data['inventory_sources'] = {}
        data['inventory_sources']['rax'] = {'url': reverse('api:inventory_source_list') + "?source=rax",
                                            'label': 'Rackspace',
                                            'failures_url': reverse('api:inventory_source_list') + "?source=rax&status=failed",
                                            'total': rax_inventory_sources.count(),
                                            'failed': rax_inventory_failed.count()}
        data['inventory_sources']['ec2'] = {'url': reverse('api:inventory_source_list') + "?source=ec2",
                                            'failures_url': reverse('api:inventory_source_list') + "?source=ec2&status=failed",
                                            'label': 'Amazon EC2',
                                            'total': ec2_inventory_sources.count(),
                                            'failed': ec2_inventory_failed.count()}

        user_groups = get_user_queryset(request.user, Group)
        groups_job_failed = (Group.objects.filter(hosts_with_active_failures__gt=0) | Group.objects.filter(groups_with_active_failures__gt=0)).count()
        groups_inventory_failed = Group.objects.filter(inventory_sources__last_job_failed=True).count()
        data['groups'] = {'url': reverse('api:group_list'),
                          'failures_url': reverse('api:group_list') + "?has_active_failures=True",
                          'total': user_groups.count(),
                          'job_failed': groups_job_failed,
                          'inventory_failed': groups_inventory_failed}

        user_hosts = get_user_queryset(request.user, Host)
        user_hosts_failed = user_hosts.filter(has_active_failures=True)
        data['hosts'] = {'url': reverse('api:host_list'),
                         'failures_url': reverse('api:host_list') + "?has_active_failures=True",
                         'total': user_hosts.count(),
                         'failed': user_hosts_failed.count()}

        user_projects = get_user_queryset(request.user, Project)
        user_projects_failed = user_projects.filter(last_job_failed=True)
        data['projects'] = {'url': reverse('api:project_list'),
                            'failures_url': reverse('api:project_list') + "?last_job_failed=True",
                            'total': user_projects.count(),
                            'failed': user_projects_failed.count()}

        git_projects = user_projects.filter(scm_type='git')
        git_failed_projects = git_projects.filter(last_job_failed=True)
        svn_projects = user_projects.filter(scm_type='svn')
        svn_failed_projects = svn_projects.filter(last_job_failed=True)
        hg_projects = user_projects.filter(scm_type='hg')
        hg_failed_projects = hg_projects.filter(last_job_failed=True)
        data['scm_types'] = {}
        data['scm_types']['git'] = {'url': reverse('api:project_list') + "?scm_type=git",
                                    'label': 'Git',
                                    'failures_url': reverse('api:project_list') + "?scm_type=git&last_job_failed=True",
                                    'total': git_projects.count(),
                                    'failed': git_failed_projects.count()}
        data['scm_types']['svn'] = {'url': reverse('api:project_list') + "?scm_type=svn",
                                    'label': 'Subversion',
                                    'failures_url': reverse('api:project_list') + "?scm_type=svn&last_job_failed=True",
                                    'total': svn_projects.count(),
                                    'failed': svn_failed_projects.count()}
        data['scm_types']['hg'] = {'url': reverse('api:project_list') + "?scm_type=hg",
                                   'label': 'Mercurial',
                                   'failures_url': reverse('api:project_list') + "?scm_type=hg&last_job_failed=True",
                                   'total': hg_projects.count(),
                                   'failed': hg_failed_projects.count()}

        user_jobs = get_user_queryset(request.user, Job)
        user_failed_jobs = user_jobs.filter(failed=True)
        data['jobs'] = {'url': reverse('api:job_list'),
                        'failure_url': reverse('api:job_list') + "?failed=True",
                        'total': user_jobs.count(),
                        'failed': user_failed_jobs.count()}

        user_list = get_user_queryset(request.user, User)
        team_list = get_user_queryset(request.user, Team)
        credential_list = get_user_queryset(request.user, Credential)
        job_template_list = get_user_queryset(request.user, JobTemplate)
        organization_list = get_user_queryset(request.user, Organization)
        data['users'] = {'url': reverse('api:user_list'),
                         'total': user_list.count()}
        data['organizations'] = {'url': reverse('api:organization_list'),
                                 'total': organization_list.count()}
        data['teams'] = {'url': reverse('api:team_list'),
                        'total': team_list.count()}
        data['credentials'] = {'url': reverse('api:credential_list'),
                               'total': credential_list.count()}
        data['job_templates'] = {'url': reverse('api:job_template_list'),
                                 'total': job_template_list.count()}
        return Response(data)

class DashboardJobsGraphView(APIView):

    view_name = "Dashboard Jobs Graphs"
    new_in_200 = True

    def get(self, request, format=None):
        period = request.QUERY_PARAMS.get('period', 'month')
        job_type = request.QUERY_PARAMS.get('job_type', 'all')

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

        start_date = datetime.datetime.utcnow()
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
            return Response({'error': 'Unknown period "%s"' % str(period)}, status=status.HTTP_400_BAD_REQUEST)

        dashboard_data = {"jobs": {"successful": [], "failed": []}}
        for element in success_qss.time_series(end_date, start_date, interval=interval):
            dashboard_data['jobs']['successful'].append([time.mktime(element[0].timetuple()),
                                                         element[1]])
        for element in failed_qss.time_series(end_date, start_date, interval=interval):
            dashboard_data['jobs']['failed'].append([time.mktime(element[0].timetuple()),
                                                     element[1]])
        return Response(dashboard_data)

class DashboardInventoryGraphView(APIView):

    view_name = "Dashboard Inventory Graphs"
    new_in_200 = True

    def get(self, request, format=None):
        period = request.QUERY_PARAMS.get('period', 'month')

        start_date = datetime.datetime.now()
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
            return Response({'error': 'Unknown period "%s"' % str(period)}, status=status.HTTP_400_BAD_REQUEST)

        user_hosts = get_user_queryset(request.user, Host)
        created_hosts = qsstats.QuerySetStats(user_hosts, 'created')
        count_hosts = user_hosts.all().count()

        dashboard_data = {'hosts': [], 'inventory': []}
        last_delta = 0
        host_data = []
        for element in created_hosts.time_series(end_date, start_date, interval=interval)[::-1]:
            host_data.append([time.mktime(element[0].timetuple()),
                                            count_hosts - last_delta])
            count_hosts -= last_delta
            last_delta = element[1]

        dashboard_data['hosts'] = host_data[::-1]

        hosts_by_inventory = user_hosts.all().values('inventory__id', 'inventory__name', 'has_active_failures', 'inventory_sources__id').annotate(Count("id"))
        inventories = {}
        for aggreg in hosts_by_inventory:
            if (aggreg['inventory__id'], aggreg['inventory__name']) not in inventories:
                inventories[(aggreg['inventory__id'], aggreg['inventory__name'])] = {}
            if aggreg['inventory_sources__id'] not in inventories[(aggreg['inventory__id'], aggreg['inventory__name'])]:
                inventories[(aggreg['inventory__id'], aggreg['inventory__name'])][aggreg['inventory_sources__id']] = {'successful': 0, 'failed': 0}
            if aggreg['has_active_failures']:
                inventories[(aggreg['inventory__id'], aggreg['inventory__name'])][aggreg['inventory_sources__id']]['failed'] = aggreg['id__count']
            else:
                inventories[(aggreg['inventory__id'], aggreg['inventory__name'])][aggreg['inventory_sources__id']]['successful'] = aggreg['id__count']
        for inventory_id, inventory_name in inventories:
            this_inventory = {'id': inventory_id, 'name': inventory_name, 'sources': []}
            for source_id in inventories[(inventory_id, inventory_name)]:
                if source_id is None:
                    continue
                i = InventorySource.objects.get(id=source_id)
                this_source = {'name': i.name, 'source': i.source,
                               'successful': inventories[(inventory_id, inventory_name)][source_id]['successful'],
                               'failed': inventories[(inventory_id, inventory_name)][source_id]['failed']}
                this_inventory['sources'].append(this_source)
            dashboard_data['inventory'].append(this_inventory)

        return Response(dashboard_data)


class ScheduleList(ListAPIView):

    view_name = "Schedules"
    model = Schedule
    serializer_class = ScheduleSerializer
    new_in_148 = True

class ScheduleDetail(RetrieveUpdateDestroyAPIView):

    model = Schedule
    serializer_class = ScheduleSerializer
    new_in_148 = True

class ScheduleUnifiedJobsList(SubListAPIView):

    model = UnifiedJob
    serializer_class = UnifiedJobSerializer
    parent_model = Schedule
    relationship = 'unifiedjob_set'
    view_name = 'Schedule Jobs List'
    new_in_148 = True

class AuthTokenView(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = AuthTokenSerializer
    model = AuthToken

    def post(self, request):
        serializer = self.serializer_class(data=request.DATA)
        if serializer.is_valid():
            request_hash = AuthToken.get_request_hash(self.request)
            try:
                token = AuthToken.objects.filter(user=serializer.object['user'],
                                                 request_hash=request_hash,
                                                 expires__gt=now())[0]
                token.refresh()
            except IndexError:
                token = AuthToken.objects.create(user=serializer.object['user'],
                                                 request_hash=request_hash)
            return Response({'token': token.key, 'expires': token.expires})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrganizationList(ListCreateAPIView):

    model = Organization
    serializer_class = OrganizationSerializer

class OrganizationDetail(RetrieveUpdateDestroyAPIView):

    model = Organization
    serializer_class = OrganizationSerializer

class OrganizationInventoriesList(SubListAPIView):

    model = Inventory
    serializer_class = InventorySerializer
    parent_model = Organization
    relationship = 'inventories'

class OrganizationUsersList(SubListCreateAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Organization
    relationship = 'users'

class OrganizationAdminsList(SubListCreateAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Organization
    relationship = 'admins'

class OrganizationProjectsList(SubListCreateAPIView):

    model = Project
    serializer_class = ProjectSerializer
    parent_model = Organization
    relationship = 'projects'

class OrganizationTeamsList(SubListCreateAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = Organization
    relationship = 'teams'
    parent_key = 'organization'

class OrganizationActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Organization
    relationship = 'activitystream_set'
    new_in_145 = True

class TeamList(ListCreateAPIView):

    model = Team
    serializer_class = TeamSerializer

class TeamDetail(RetrieveUpdateDestroyAPIView):

    model = Team
    serializer_class = TeamSerializer

class TeamUsersList(SubListCreateAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Team
    relationship = 'users'

class TeamPermissionsList(SubListCreateAPIView):

    model = Permission
    serializer_class = PermissionSerializer
    parent_model = Team
    relationship = 'permissions'
    parent_key = 'team'

    def get_queryset(self):
        # FIXME: Default get_queryset should handle this.
        team = Team.objects.get(pk=self.kwargs['pk'])
        base = Permission.objects.filter(team = team)
        #if Team.can_user_administrate(self.request.user, team, None):
        if self.request.user.can_access(Team, 'change', team, None):
            return base
        elif team.users.filter(pk=self.request.user.pk).count() > 0:
            return base
        raise PermissionDenied()

class TeamProjectsList(SubListCreateAPIView):

    model = Project
    serializer_class = ProjectSerializer
    parent_model = Team
    relationship = 'projects'

class TeamCredentialsList(SubListCreateAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    parent_model = Team
    relationship = 'credentials'
    parent_key = 'team'

class TeamActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Team
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(team=parent) |
                         Q(project__in=parent.projects.all()) |
                         Q(credential__in=parent.credentials.all()) |
                         Q(permission__in=parent.permissions.all()))


class ProjectList(ListCreateAPIView):

    model = Project
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        # Not optimal, but make sure the project status and last_updated fields
        # are up to date here...
        projects_qs = Project.objects.filter(active=True)
        projects_qs = projects_qs.select_related('current_update', 'last_updated')
        for project in projects_qs:
            project._set_status_and_last_job_run()
        return super(ProjectList, self).get(request, *args, **kwargs)

class ProjectDetail(RetrieveUpdateDestroyAPIView):

    model = Project
    serializer_class = ProjectSerializer

    def destroy(self, request, *args, **kwargs):
        obj = Project.objects.get(pk=kwargs['pk'])
        can_delete = request.user.can_access(Project, 'delete', obj)
        if not can_delete:
            raise PermissionDenied("Cannot delete project")
        for pu in obj.project_updates.filter(status__in=['new', 'pending', 'waiting', 'running']):
            pu.cancel()
        return super(ProjectDetail, self).destroy(request, *args, **kwargs)

class ProjectPlaybooks(RetrieveAPIView):

    model = Project
    serializer_class = ProjectPlaybooksSerializer

class ProjectOrganizationsList(SubListCreateAPIView):

    model = Organization
    serializer_class = OrganizationSerializer
    parent_model = Project
    relationship = 'organizations'

class ProjectTeamsList(SubListCreateAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = Project
    relationship = 'teams'

class ProjectSchedulesList(SubListCreateAPIView):

    view_name = "Project Schedules"

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = Project
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_148 = True

class ProjectActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Project
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        if parent is None:
            return qs
        elif parent.credential is None:
            return qs.filter(project=parent)
        return qs.filter(Q(project=parent) | Q(credential__in=parent.credential))


class ProjectUpdatesList(SubListAPIView):

    model = ProjectUpdate
    serializer_class = ProjectUpdateSerializer
    parent_model = Project
    relationship = 'project_updates'
    new_in_13 = True

class ProjectUpdateView(RetrieveAPIView):

    model = Project
    serializer_class = ProjectUpdateViewSerializer
    new_in_13 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_update:
            project_update = obj.update()
            if not project_update:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            else:
                headers = {'Location': project_update.get_absolute_url()}
                return Response({'project_update': project_update.id},
                                headers=headers,
                                status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class ProjectUpdateDetail(RetrieveDestroyAPIView):

    model = ProjectUpdate
    serializer_class = ProjectUpdateSerializer
    new_in_13 = True

class ProjectUpdateCancel(RetrieveAPIView):

    model = ProjectUpdate
    serializer_class = ProjectUpdateCancelSerializer
    is_job_cancel = True
    new_in_13 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            result = obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class UserList(ListCreateAPIView):

    model = User
    serializer_class = UserSerializer

class UserMeList(ListAPIView):

    model = User
    serializer_class = UserSerializer
    view_name = 'Me'

    def get_queryset(self):
        return self.model.objects.filter(pk=self.request.user.pk)

class UserTeamsList(SubListAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = User
    relationship = 'teams'

class UserPermissionsList(SubListCreateAPIView):

    model = Permission
    serializer_class = PermissionSerializer
    parent_model = User
    relationship = 'permissions'
    parent_key = 'user'

class UserProjectsList(SubListAPIView):

    model = Project
    serializer_class = ProjectSerializer
    parent_model = User
    relationship = 'projects'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(teams__in=parent.teams.distinct())

class UserCredentialsList(SubListCreateAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    parent_model = User
    relationship = 'credentials'
    parent_key = 'user'

class UserOrganizationsList(SubListAPIView):

    model = Organization
    serializer_class = OrganizationSerializer
    parent_model = User
    relationship = 'organizations'

class UserAdminOfOrganizationsList(SubListAPIView):

    model = Organization
    serializer_class = OrganizationSerializer
    parent_model = User
    relationship = 'admin_of_organizations'

class UserActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = User
    relationship = 'activitystream_set'
    new_in_145 = True

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
        obj = User.objects.get(pk=kwargs['pk'])
        can_change = request.user.can_access(User, 'change', obj, request.DATA)
        can_admin = request.user.can_access(User, 'admin', obj, request.DATA)
        if can_change and not can_admin:
            admin_only_edit_fields = ('last_name', 'first_name', 'username',
                                      'is_active', 'is_superuser')
            changed = {}
            for field in admin_only_edit_fields:
                left = getattr(obj, field, None)
                right = request.DATA.get(field, None)
                if left is not None and right is not None and left != right:
                    changed[field] = (left, right)
            if changed:
                raise PermissionDenied('Cannot change %s' % ', '.join(changed.keys()))

    def destroy(self, request, *args, **kwargs):
        obj = User.objects.get(pk=kwargs['pk'])
        can_delete = request.user.can_access(User, 'delete', obj)
        if not can_delete:
            raise PermissionDenied('Cannot delete user')
        for own_credential in Credential.objects.filter(user=obj):
            own_credential.mark_inactive()
        return super(UserDetail, self).destroy(request, *args, **kwargs)

class CredentialList(ListCreateAPIView):

    model = Credential
    serializer_class = CredentialSerializer

class CredentialDetail(RetrieveUpdateDestroyAPIView):

    model = Credential
    serializer_class = CredentialSerializer

class CredentialActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Credential
    relationship = 'activitystream_set'
    new_in_145 = True

class PermissionDetail(RetrieveUpdateDestroyAPIView):

    model = Permission
    serializer_class = PermissionSerializer

class InventoryScriptList(ListCreateAPIView):

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer

class InventoryScriptDetail(RetrieveUpdateDestroyAPIView):

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = request.user.can_access(self.model, 'delete', obj)
        if not can_delete:
            raise PermissionDenied("Cannot delete inventory script")
        for inv_src in InventorySource.objects.filter(source_script=obj):
            inv_src.source_script = None
            inv_src.save()
        return super(InventoryScriptDetail, self).destroy(request, *args, **kwargs)

class InventoryList(ListCreateAPIView):

    model = Inventory
    serializer_class = InventorySerializer

class InventoryDetail(RetrieveUpdateDestroyAPIView):

    model = Inventory
    serializer_class = InventorySerializer

    def destroy(self, request, *args, **kwargs):
        with ignore_inventory_computed_fields():
            with ignore_inventory_group_removal():
                return super(InventoryDetail, self).destroy(request, *args, **kwargs)

class InventoryActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Inventory
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(inventory=parent) | Q(host__in=parent.hosts.all()) | Q(group__in=parent.groups.all()))


class HostList(ListCreateAPIView):

    model = Host
    serializer_class = HostSerializer

class HostDetail(RetrieveUpdateDestroyAPIView):

    model = Host
    serializer_class = HostSerializer

class InventoryHostsList(SubListCreateAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = Inventory
    relationship = 'hosts'
    parent_key = 'inventory'

class HostGroupsList(SubListCreateAPIView):
    ''' the list of groups a host is directly a member of '''

    model = Group
    serializer_class = GroupSerializer
    parent_model = Host
    relationship = 'groups'

class HostAllGroupsList(SubListAPIView):
    ''' the list of all groups of which the host is directly or indirectly a member '''

    model = Group
    serializer_class = GroupSerializer
    parent_model = Host
    relationship = 'groups'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        sublist_qs = parent.all_groups.distinct()
        return qs & sublist_qs

class HostInventorySourcesList(SubListAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Host
    relationship = 'inventory_sources'
    new_in_148 = True

class HostActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Host
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(host=parent) | Q(inventory=parent.inventory))


class GroupList(ListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer

class GroupChildrenList(SubListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Group
    relationship = 'children'

    def unattach(self, request, *args, **kwargs):
        sub_id = request.DATA.get('id', None)
        if sub_id is not None:
            return super(GroupChildrenList, self).unattach(request, *args, **kwargs)
        parent = self.get_parent_object()
        parent.mark_inactive()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _unattach(self, request, *args, **kwargs): # FIXME: Disabled for now for UI support.
        '''
        Special case for disassociating a child group from the parent. If the
        child group has no more parents, then automatically mark it inactive.
        '''
        sub_id = request.DATA.get('id', None)
        if not sub_id:
            data = dict(msg='"id" is required to disassociate')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        parent = self.get_parent_object()
        parent_key = getattr(self, 'parent_key', None)
        relationship = getattr(parent, self.relationship)
        sub = get_object_or_400(self.model, pk=sub_id)

        if not request.user.can_access(self.parent_model, 'unattach', parent,
                                       sub, self.relationship):
            raise PermissionDenied()

        if sub.parents.filter(active=True).exclude(pk=parent.pk).count() == 0:
            sub.mark_inactive()
        else:
            relationship.remove(sub)

        return Response(status=status.HTTP_204_NO_CONTENT)

class GroupPotentialChildrenList(SubListAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Group
    new_in_14 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        qs = qs.filter(inventory__pk=parent.inventory.pk)
        except_pks = set([parent.pk])
        except_pks.update(parent.all_parents.values_list('pk', flat=True))
        except_pks.update(parent.all_children.values_list('pk', flat=True))
        return qs.exclude(pk__in=except_pks)

class GroupHostsList(SubListCreateAPIView):
    ''' the list of hosts directly below a group '''

    model = Host
    serializer_class = HostSerializer
    parent_model = Group
    relationship = 'hosts'

    def create(self, request, *args, **kwargs):
        parent_group = Group.objects.get(id=self.kwargs['pk'])
        existing_hosts = Host.objects.filter(inventory=parent_group.inventory, name=request.DATA['name'])
        if existing_hosts.count() > 0 and ('variables' not in request.DATA or \
                                           request.DATA['variables'] == '' or \
                                           request.DATA['variables'] == '{}' or \
                                           request.DATA['variables'] == '---'):
            request.DATA['id'] = existing_hosts[0].id
            return self.attach(request, *args, **kwargs)
        return super(GroupHostsList, self).create(request, *args, **kwargs)

class GroupAllHostsList(SubListAPIView):
    ''' the list of all hosts below a group, even including subgroups '''

    model = Host
    serializer_class = HostSerializer
    parent_model = Group
    relationship = 'hosts'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        sublist_qs = parent.all_hosts.distinct()
        return qs & sublist_qs

class GroupInventorySourcesList(SubListAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Group
    relationship = 'inventory_sources'
    new_in_148 = True

class GroupActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Group
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(group=parent) | Q(host__in=parent.hosts.all()))

class GroupDetail(RetrieveUpdateDestroyAPIView):

    model = Group
    serializer_class = GroupSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        # FIXME: Why isn't the active check being caught earlier by RBAC?
        if getattr(obj, 'active', True) == False:
            raise Http404()
        if getattr(obj, 'is_active', True) == False:
            raise Http404()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        if hasattr(obj, 'mark_inactive'):
            obj.mark_inactive_recursive()
        return Response(status=status.HTTP_204_NO_CONTENT)

class InventoryGroupsList(SubListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Inventory
    relationship = 'groups'
    parent_key = 'inventory'

class InventoryRootGroupsList(SubListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Inventory
    relationship = 'groups'
    parent_key = 'inventory'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
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
    authentication_classes = [JobTaskAuthentication] + \
                             api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (JobTaskPermission,)
    filter_backends = ()

    def retrieve(self, request, *args, **kwargs):
        self.object = self.get_object()
        hostname = request.QUERY_PARAMS.get('host', '')
        hostvars = bool(request.QUERY_PARAMS.get('hostvars', ''))
        show_all = bool(request.QUERY_PARAMS.get('all', ''))
        if show_all:
            hosts_q = dict(active=True)
        else:
            hosts_q = dict(active=True, enabled=True)
        if hostname:
            host = get_object_or_404(self.object.hosts, name=hostname, **hosts_q)
            data = host.variables_dict
        else:
            data = SortedDict()
            if self.object.variables_dict:
                all_group = data.setdefault('all', SortedDict())
                all_group['vars'] = self.object.variables_dict

            # Add hosts without a group to the all group.
            groupless_hosts_qs = self.object.hosts.filter(groups__isnull=True, **hosts_q).order_by('name')
            groupless_hosts = list(groupless_hosts_qs.values_list('name', flat=True))
            if groupless_hosts:
                all_group = data.setdefault('all', SortedDict())
                all_group['hosts'] = groupless_hosts

            # Build in-memory mapping of groups and their hosts.
            group_hosts_kw = dict(group__inventory_id=self.object.id, group__active=True,
                                  host__inventory_id=self.object.id, host__active=True)
            if 'enabled' in hosts_q:
                group_hosts_kw['host__enabled'] = hosts_q['enabled']
            group_hosts_qs = Group.hosts.through.objects.filter(**group_hosts_kw)
            group_hosts_qs = group_hosts_qs.order_by('host__name')
            group_hosts_qs = group_hosts_qs.values_list('group_id', 'host_id', 'host__name')
            group_hosts_map = {}
            for group_id, host_id, host_name in group_hosts_qs:
                group_hostnames = group_hosts_map.setdefault(group_id, [])
                group_hostnames.append(host_name)
        
            # Build in-memory mapping of groups and their children.
            group_parents_qs = Group.parents.through.objects.filter(
                from_group__inventory_id=self.object.id, from_group__active=True,
                to_group__inventory_id=self.object.id, to_group__active=True,
            )
            group_parents_qs = group_parents_qs.order_by('from_group__name')
            group_parents_qs = group_parents_qs.values_list('from_group_id', 'from_group__name', 'to_group_id')
            group_children_map = {}
            for from_group_id, from_group_name, to_group_id in group_parents_qs:
                group_children = group_children_map.setdefault(to_group_id, [])
                group_children.append(from_group_name)

            # Now use in-memory maps to build up group info.
            for group in self.object.groups.filter(active=True):
                group_info = SortedDict()
                group_info['hosts'] = group_hosts_map.get(group.id, [])
                group_info['children'] = group_children_map.get(group.id, [])
                group_info['vars'] = group.variables_dict
                data[group.name] = group_info

            if hostvars:
                data.setdefault('_meta', SortedDict())
                data['_meta'].setdefault('hostvars', SortedDict())
                for host in self.object.hosts.filter(**hosts_q):
                    data['_meta']['hostvars'][host.name] = host.variables_dict

            # workaround for Ansible inventory bug (github #3687), localhost
            # must be explicitly listed in the all group for dynamic inventory
            # scripts to pick it up.
            localhost_names = ('localhost', '127.0.0.1', '::1')
            localhosts_qs = self.object.hosts.filter(name__in=localhost_names,
                                                     **hosts_q)
            localhosts = list(localhosts_qs.values_list('name', flat=True))
            if localhosts:
                all_group = data.setdefault('all', SortedDict())
                all_group_hosts = all_group.get('hosts', [])
                all_group_hosts.extend(localhosts)
                all_group['hosts'] = sorted(set(all_group_hosts))

        return Response(data)

class InventoryTreeView(RetrieveAPIView):

    model = Inventory
    serializer_class = GroupTreeSerializer
    filter_backends = ()
    new_in_13 = True

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
        group_children_map = inventory.get_group_children_map(active=True)
        root_group_pks = inventory.root_groups.filter(active=True).order_by('name').values_list('pk', flat=True)
        groups_qs = inventory.groups.filter(active=True)
        groups_qs = groups_qs.select_related('inventory')
        groups_qs = groups_qs.prefetch_related('inventory_source')
        all_group_data = GroupSerializer(groups_qs, many=True).data
        all_group_data_map = dict((x['id'], x) for x in all_group_data)
        tree_data = [all_group_data_map[x] for x in root_group_pks]
        for group_data in tree_data:
            self._populate_group_children(group_data, all_group_data_map,
                                          group_children_map)
        return Response(tree_data)

    def get_description_context(self):
        d = super(InventoryTreeView, self).get_description_context()
        d.update({
            'serializer_fields': GroupTreeSerializer().metadata(),
        })
        return d

class InventoryInventorySourcesList(SubListAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Inventory
    relationship = None # Not defined since using get_queryset().
    view_name = 'Inventory Source List'
    new_in_14 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(inventory__pk=parent.pk) |
                         Q(group__inventory__pk=parent.pk))

class InventorySourceList(ListAPIView):

     model = InventorySource
     serializer_class = InventorySourceSerializer
     new_in_14 = True

class InventorySourceDetail(RetrieveUpdateAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    new_in_14 = True

    def destroy(self, request, *args, **kwargs):
        obj = InventorySource.objects.get(pk=kwargs['pk'])
        can_delete = request.user.can_access(InventorySource, 'delete', obj)
        if not can_delete:
            raise PermissionDenied("Cannot delete inventory source")
        for pu in obj.inventory_updates.filter(status__in=['new', 'pending', 'waiting', 'running']):
            pu.cancel()
        return super(InventorySourceDetail, self).destroy(request, *args, **kwargs)

class InventorySourceSchedulesList(SubListCreateAPIView):

    view_name = "Inventory Source Schedules"

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = InventorySource
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_148 = True

class InventorySourceActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = InventorySource
    relationship = 'activitystream_set'
    new_in_145 = True

class InventorySourceHostsList(SubListAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = InventorySource
    relationship = 'hosts'
    new_in_148 = True

class InventorySourceGroupsList(SubListAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = InventorySource
    relationship = 'groups'
    new_in_148 = True

class InventorySourceUpdatesList(SubListAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateSerializer
    parent_model = InventorySource
    relationship = 'inventory_updates'
    new_in_14 = True

class InventorySourceUpdateView(RetrieveAPIView):

    model = InventorySource
    serializer_class = InventorySourceUpdateSerializer
    is_job_start = True
    new_in_14 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_update:
            inventory_update = obj.update()
            if not inventory_update:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            else:
                headers = {'Location': inventory_update.get_absolute_url()}
                return Response(dict(inventory_update=inventory_update.id), status=status.HTTP_202_ACCEPTED, headers=headers)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class InventoryUpdateDetail(RetrieveDestroyAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateSerializer
    new_in_14 = True

class InventoryUpdateCancel(RetrieveAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateCancelSerializer
    is_job_cancel = True
    new_in_14 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            result = obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class JobTemplateList(ListCreateAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer

class JobTemplateDetail(RetrieveUpdateDestroyAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer

    def destroy(self, request, *args, **kwargs):
        obj = JobTemplate.objects.get(pk=kwargs['pk'])
        can_delete = request.user.can_access(JobTemplate, 'delete', obj)
        if not can_delete:
            raise PermissionDenied("Cannot delete job template")
        for pu in obj.jobs.filter(status__in=['new', 'pending', 'waiting', 'running']):
            pu.cancel()
        return super(JobTemplateDetail, self).destroy(request, *args, **kwargs)


class JobTemplateLaunch(GenericAPIView):

    model = JobTemplate
    # FIXME: Add serializer class to define fields in OPTIONS request!
    is_job_start = True

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {}
        data['can_start_without_user_input'] = obj.can_start_without_user_input()
        data['passwords_needed_to_start'] = obj.passwords_needed_to_start
        data['ask_variables_on_launch'] = obj.ask_variables_on_launch
        data['variables_needed_to_start'] = obj.variables_needed_to_start
        data['credential_needed_to_start'] = obj.credential is None
        data['survey_enabled'] = obj.survey_enabled
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()
        if obj.survey_enabled:
            if request.DATA == "":
                request_data = {}
            else:
                request_data = request.DATA
            validation_errors = obj.survey_variable_validation(request_data.get('extra_vars', {}))
            if validation_errors:
                return Response(dict(variables_needed_to_start=validation_errors),
                                status=status.HTTP_400_BAD_REQUEST)
        if obj.credential is None and ('credential' not in request.DATA and 'credential_id' not in request.DATA):
            return Response(dict(errors="Credential not provided"), status=status.HTTP_400_BAD_REQUEST)
        if obj.project is None or not obj.project.active:
            return Response(dict(errors="Job Template Project is missing or undefined"), status=status.HTTP_400_BAD_REQUEST)
        if obj.inventory is None or not obj.inventory.active:
            return Response(dict(errors="Job Template Inventory is missing or undefined"), status=status.HTTP_400_BAD_REQUEST)
        new_job = obj.create_unified_job(**request.DATA)
        result = new_job.signal_start(**request.DATA)
        if not result:
            data = dict(passwords_needed_to_start=new_job.passwords_needed_to_start)
            new_job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = dict(job=new_job.id)
            return Response(data, status=status.HTTP_202_ACCEPTED)

class JobTemplateSchedulesList(SubListCreateAPIView):

    view_name = "Job Template Schedules"

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = JobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_148 = True

class JobTemplateSurveySpec(GenericAPIView):

    model = JobTemplate
    parent_model = JobTemplate
    # FIXME: Add serializer class to define fields in OPTIONS request!

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.survey_enabled:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(obj.survey_spec)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'change', obj, None):
            raise PermissionDenied()
        try:
            obj.survey_spec = json.dumps(request.DATA)
        except ValueError, e:
            return Response(dict(error="Invalid JSON when parsing survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if "name" not in obj.survey_spec:
            return Response(dict(error="'name' missing from survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if "description" not in obj.survey_spec:
            return Response(dict(error="'description' missing from survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if "spec" not in obj.survey_spec:
            return Response(dict(error="'spec' missing from survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if type(obj.survey_spec["spec"]) != list:
            return Response(dict(error="'spec' must be a list of items"), status=status.HTTP_400_BAD_REQUEST)
        if len(obj.survey_spec["spec"]) < 1:
            return Response(dict(error="'spec' doesn't contain any items"), status=status.HTTP_400_BAD_REQUEST)
        idx = 0
        for survey_item in obj.survey_spec["spec"]:
            if type(survey_item) != dict:
                return Response(dict(error="survey element %s is not a json object" % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if "type" not in survey_item:
                return Response(dict(error="'type' missing from survey element %s" % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if "question_name" not in survey_item:
                return Response(dict(error="'question_name' missing from survey element %s" % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if "variable" not in survey_item:
                return Response(dict(error="'variable' missing from survey element %s" % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if "required" not in survey_item:
                return Response(dict(error="'required' missing from survey element %s" % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            idx += 1
        obj.save()
        return Response()

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        obj.survey_spec = {}
        obj.save()
        return Response()

class JobTemplateActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = JobTemplate
    relationship = 'activitystream_set'
    new_in_145 = True

class JobTemplateCallback(GenericAPIView):

    model = JobTemplate
    # FIXME: Add serializer class to define fields in OPTIONS request!
    permission_classes = (JobTemplateCallbackPermission,)

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
        qs = obj.inventory.hosts.filter(active=True)
        # First try for an exact match on the name.
        try:
            return set([qs.get(name__in=remote_hosts)])
        except (Host.DoesNotExist, Host.MultipleObjectsReturned):
            pass
        # Next, try matching based on name or ansible_ssh_host variable.
        matches = set()
        for host in qs:
            ansible_ssh_host = host.variables_dict.get('ansible_ssh_host', '')
            if ansible_ssh_host in remote_hosts:
                matches.add(host)
            # FIXME: Not entirely sure if this statement will ever be needed?
            if host.name != ansible_ssh_host and host.name in remote_hosts:
                matches.add(host)
        if len(matches) == 1:
            return matches
        # Try to resolve forward addresses for each host to find matches.
        for host in qs:
            hostnames = set([host.name])
            ansible_ssh_host = host.variables_dict.get('ansible_ssh_host', '')
            if ansible_ssh_host:
                hostnames.add(ansible_ssh_host)
            for hostname in hostnames:
                try:
                    result = socket.getaddrinfo(hostname, None)
                    possible_ips = set(x[4][0] for x in result)
                    possible_ips.discard(hostname)
                    if possible_ips and possible_ips & remote_hosts:
                        matches.add(host)
                except socket.gaierror:
                    pass
        # Return all matches found.
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
        # Permission class should have already validated host_config_key.
        job_template = self.get_object()
        # Attempt to find matching hosts based on remote address.
        matching_hosts = self.find_matching_hosts()
        # If the host is not found, update the inventory before trying to
        # match again.
        inventory_sources_already_updated = []
        if len(matching_hosts) != 1:
            inventory_sources = job_template.inventory.inventory_sources.filter(active=True, update_on_launch=True)
            inventory_update_pks = set()
            for inventory_source in inventory_sources:
                if inventory_source.needs_update_on_launch:
                    # FIXME: Doesn't check for any existing updates.
                    inventory_update = inventory_source.create_inventory_update(launch_type='callback')
                    inventory_update.signal_start()
                    inventory_update_pks.add(inventory_update.pk)
            inventory_update_qs = InventoryUpdate.objects.filter(pk__in=inventory_update_pks, status__in=('pending', 'waiting', 'running'))
            # Poll for the inventory updates we've started to complete.
            while inventory_update_qs.count():
                time.sleep(1.0)
                transaction.commit()
            # Ignore failed inventory updates here, only add successful ones
            # to the list to be excluded when running the job.
            for inventory_update in InventoryUpdate.objects.filter(pk__in=inventory_update_pks, status='successful'):
                inventory_sources_already_updated.append(inventory_update.inventory_source_id)
            matching_hosts = self.find_matching_hosts()
        # Check matching hosts.
        if not matching_hosts:
            data = dict(msg='No matching host could be found!')
            # FIXME: Log!
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        elif len(matching_hosts) > 1:
            data = dict(msg='Multiple hosts matched the request!')
            # FIXME: Log!
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            host = list(matching_hosts)[0]
        if not job_template.can_start_without_user_input():
            data = dict(msg='Cannot start automatically, user input required!')
            # FIXME: Log!
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        limit = ':&'.join(filter(None, [job_template.limit, host.name]))

        # NOTE: We limit this to one job waiting due to this: https://trello.com/c/yK36dGWp
        if Job.objects.filter(status__in=['pending', 'waiting', 'running'], job_template=job_template,
                              limit=limit).count() > 0:
            data = dict(msg='Host callback job already pending')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Everything is fine; actually create the job.
        with transaction.atomic():
            job = job_template.create_job(limit=limit, launch_type='callback')

        # Send a signal to celery that the job should be started.
        isau = inventory_sources_already_updated
        result = job.signal_start(inventory_sources_already_updated=isau)
        if not result:
            data = dict(msg='Error starting job!')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Return the location of the new job.
        headers = {'Location': job.get_absolute_url()}
        return Response(status=status.HTTP_202_ACCEPTED, headers=headers)


class JobTemplateJobsList(SubListCreateAPIView):

    model = Job
    serializer_class = JobListSerializer
    parent_model = JobTemplate
    relationship = 'jobs'
    parent_key = 'job_template'

class SystemJobTemplateList(ListAPIView):

    model = SystemJobTemplate
    serializer_class = SystemJobTemplateSerializer

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return super(SystemJobTemplateList, self).get(request, *args, **kwargs)

class SystemJobTemplateDetail(RetrieveAPIView):

    model = SystemJobTemplate
    serializer_class = SystemJobTemplateSerializer

class SystemJobTemplateLaunch(GenericAPIView):

    model = SystemJobTemplate
    # FIXME: Add serializer class to define fields in OPTIONS request!

    def get(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()
            
        new_job = obj.create_unified_job(**request.DATA)
        result = new_job.signal_start(**request.DATA)
        data = dict(system_job=new_job.id)
        return Response(data, status=status.HTTP_202_ACCEPTED)

class SystemJobTemplateSchedulesList(SubListCreateAPIView):

    view_name = "System Job Template Schedules"

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = SystemJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'

    def post(self, request, *args, **kwargs):
        system_job = self.get_parent_object()
        if system_job.schedules.filter(active=True).count() > 0:
            return Response({"error": "Multiple schedules for Systems Jobs is not allowed"}, status=status.HTTP_400_BAD_REQUEST)
        return super(SystemJobTemplateSchedulesList, self).post(request, *args, **kwargs)

class SystemJobTemplateJobsList(SubListAPIView):

    model = SystemJob
    serializer_class = SystemJobListSerializer
    parent_model = SystemJobTemplate
    relationship = 'jobs'
    parent_key = 'system_job_template'

class JobList(ListCreateAPIView):

    model = Job
    serializer_class = JobListSerializer

class JobDetail(RetrieveUpdateDestroyAPIView):

    model = Job
    serializer_class = JobSerializer

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        # Only allow changes (PUT/PATCH) when job status is "new".
        if obj.status != 'new':
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super(JobDetail, self).update(request, *args, **kwargs)

class JobActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Job
    relationship = 'activitystream_set'
    new_in_145 = True

class JobStart(GenericAPIView):

    model = Job
    # FIXME: Add serializer class to define fields in OPTIONS request!
    is_job_start = True

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = dict(
            can_start=obj.can_start,
        )
        if obj.can_start:
            data['passwords_needed_to_start'] = obj.passwords_needed_to_start
            data['ask_variables_on_launch'] = obj.ask_variables_on_launch
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()
        if obj.can_start:
            result = obj.signal_start(**request.DATA)
            if not result:
                data = dict(passwords_needed_to_start=obj.passwords_needed_to_start)
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class JobCancel(RetrieveAPIView):

    model = Job
    serializer_class = JobCancelSerializer
    is_job_cancel = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            result = obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class JobRelaunch(GenericAPIView):

    model = Job
    # FIXME: Add serializer class to define fields in OPTIONS request!

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(JobRelaunch, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = {}
        data['passwords_needed_to_start'] = obj.passwords_needed_to_start
        #data['ask_variables_on_launch'] = obj.ask_variables_on_launch
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()
        new_job = obj.copy()
        result = new_job.signal_start(**request.DATA)
        if not result:
            data = dict(passwords_needed_to_start=obj.passwords_needed_to_start)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = dict(job=new_job.id)
            return Response(data, status=status.HTTP_202_ACCEPTED)


class BaseJobHostSummariesList(SubListAPIView):

    model = JobHostSummary
    serializer_class = JobHostSummarySerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_host_summaries'
    view_name = 'Job Host Summaries List'

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

class JobEventDetail(RetrieveAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer

class JobEventChildrenList(SubListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    parent_model = JobEvent
    relationship = 'children'
    view_name = 'Job Event Children List'

class JobEventHostsList(SubListAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = JobEvent
    relationship = 'hosts'
    view_name = 'Job Event Hosts List'

class BaseJobEventsList(SubListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_events'
    view_name = 'Job Events List'

class HostJobEventsList(BaseJobEventsList):

    parent_model = Host

class GroupJobEventsList(BaseJobEventsList):

    parent_model = Group

class JobJobEventsList(BaseJobEventsList):

    parent_model = Job
    authentication_classes = [JobTaskAuthentication] + \
                             api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (JobTaskPermission,)

    # Post allowed for job event callback only.
    def post(self, request, *args, **kwargs):
        parent_obj = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        data = request.DATA.copy()
        data['job'] = parent_obj.pk
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.pre_save(serializer.object)
            self.object = serializer.save(force_insert=True)
            self.post_save(self.object, created=True)
            headers = {'Location': serializer.data['url']}
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobJobPlaysList(BaseJobEventsList):

    parent_model = Job
    view_name = 'Job Plays List'
    authentication_classes = [JobTaskAuthentication] + \
                             api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (JobTaskPermission,)
    new_in_200 = True

    @paginated
    def get(self, request, limit, offset, ordering, *args, **kwargs):
        all_plays = []
        job = Job.objects.filter(pk=self.kwargs['pk'])
        if not job.exists():
            return ({'detail': 'job not found'}, -1, status.HTTP_404_NOT_FOUND)
        job = job[0]

        # Put together a queryset for relevant job events.
        qs = job.job_events.filter(event='playbook_on_play_start')
        if ordering is not None:
            qs = qs.order_by(ordering)

        # This is a bit of a special case for filtering requested by the UI
        # doing this here for the moment until/unless we need to implement more
        # complex filtering (since we aren't under a serializer)

        if "id__in" in request.QUERY_PARAMS:
            qs = qs.filter(id__in=[int(filter_id) for filter_id in request.QUERY_PARAMS["id__in"].split(",")])
        elif "id__gt" in request.QUERY_PARAMS:
            qs = qs.filter(id__gt=request.QUERY_PARAMS['id__gt'])
        elif "id__lt" in request.QUERY_PARAMS:
            qs = qs.filter(id__lt=request.QUERY_PARAMS['id__lt'])
        if "failed" in request.QUERY_PARAMS:
            qs = qs.filter(failed=(request.QUERY_PARAMS['failed'].lower() == 'true'))
        if "play__icontains" in request.QUERY_PARAMS:
            qs = qs.filter(play__icontains=request.QUERY_PARAMS['play__icontains'])

        count = qs.count()

        # Iterate over the relevant play events and get the details.
        for play_event in qs[offset:offset + limit]:
            play_details = dict(id=play_event.id, play=play_event.play, started=play_event.created, failed=play_event.failed, changed=play_event.changed)
            event_aggregates = JobEvent.objects.filter(parent__in=play_event.children.all()).values("event").annotate(Count("id")).order_by()
            change_aggregates = JobEvent.objects.filter(parent__in=play_event.children.all(), event='runner_on_ok').values("changed").annotate(Count("id")).order_by()
            failed_count = 0
            ok_count = 0
            changed_count = 0
            skipped_count = 0
            unreachable_count = 0
            for event_aggregate in event_aggregates:
                if event_aggregate['event'] == 'runner_on_failed':
                    failed_count += event_aggregate['id__count']
                elif event_aggregate['event'] == 'runner_on_error':
                    failed_count += event_aggregate['id_count']
                elif event_aggregate['event'] == 'runner_on_skipped':
                    skipped_count = event_aggregate['id__count']
                elif event_aggregate['event'] == 'runner_on_unreachable':
                    unreachable_count = event_aggregate['id__count']
            for change_aggregate in change_aggregates:
                if change_aggregate['changed'] == False:
                    ok_count = change_aggregate['id__count']
                else:
                    changed_count = change_aggregate['id__count']
            play_details['related'] = {'job_event': reverse('api:job_event_detail', args=(play_event.pk,))}
            play_details['type'] = 'job_event'
            play_details['ok_count'] = ok_count
            play_details['failed_count'] = failed_count
            play_details['changed_count'] = changed_count
            play_details['skipped_count'] = skipped_count
            play_details['unreachable_count'] = unreachable_count
            all_plays.append(play_details)

        # Done; return the plays and the total count.
        return all_plays, count, None


class JobJobTasksList(BaseJobEventsList):
    """A view for displaying aggregate data about tasks within a job
    and their completion status.
    """
    parent_model = Job
    authentication_classes = [JobTaskAuthentication] + \
                             api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (JobTaskPermission,)
    view_name = 'Job Play Tasks List'
    new_in_200 = True

    @paginated
    def get(self, request, limit, offset, ordering, *args, **kwargs):
        """Return aggregate data about each of the job tasks that is:
          - an immediate child of the job event
          - corresponding to the spinning up of a new task or playbook
        """
        results = []

        # Get the job and the parent task.
        # If there's no event ID specified, this will return a 404.
        job = Job.objects.filter(pk=self.kwargs['pk'])
        if not job.exists():
            return ({'detail': 'job not found'}, -1, status.HTTP_404_NOT_FOUND)
        job = job[0]

        if 'event_id' not in request.QUERY_PARAMS:
            return ({'detail': '"event_id" not provided'}, -1, status.HTTP_400_BAD_REQUEST)

        parent_task = job.job_events.filter(pk=int(request.QUERY_PARAMS.get('event_id', -1)))
        if not parent_task.exists():
            return ({'detail': 'parent event not found'}, -1, status.HTTP_404_NOT_FOUND)
        parent_task = parent_task[0]

        # Some events correspond to a playbook or task starting up,
        # and these are what we're interested in here.
        STARTING_EVENTS = ('playbook_on_task_start', 'playbook_on_setup')

        # We need to pull information about each start event.
        #
        # This is super tricky, because this table has a one-to-many
        # relationship with itself (parent-child), and we're getting
        # information for an arbitrary number of children. This means we
        # need stats on grandchildren, sorted by child. 
        queryset = (JobEvent.objects.filter(parent__parent=parent_task,
                                            parent__event__in=STARTING_EVENTS)
                                    .values('parent__id', 'event', 'changed')
                                    .annotate(num=Count('event'))
                                    .order_by('parent__id'))

        # The data above will come back in a list, but we are going to
        # want to access it based on the parent id, so map it into a
        # dictionary.
        data = {}
        for line in queryset[offset:offset + limit]:
            parent_id = line.pop('parent__id')
            data.setdefault(parent_id, [])
            data[parent_id].append(line)

        # Iterate over the start events and compile information about each one
        # using their children.
        qs = parent_task.children.filter(event__in=STARTING_EVENTS,
                                         id__in=data.keys())

        # This is a bit of a special case for id filtering requested by the UI
        # doing this here for the moment until/unless we need to implement more
        # complex filtering (since we aren't under a serializer)

        if "id__in" in request.QUERY_PARAMS:
            qs = qs.filter(id__in=[int(filter_id) for filter_id in request.QUERY_PARAMS["id__in"].split(",")])
        elif "id__gt" in request.QUERY_PARAMS:
            qs = qs.filter(id__gt=request.QUERY_PARAMS['id__gt'])
        elif "id__lt" in request.QUERY_PARAMS:
            qs = qs.filter(id__lt=request.QUERY_PARAMS['id__lt'])
        if "failed" in request.QUERY_PARAMS:
            qs = qs.filter(failed=(request.QUERY_PARAMS['failed'].lower() == 'true'))
        if "task__icontains" in request.QUERY_PARAMS:
            qs = qs.filter(task__icontains=request.QUERY_PARAMS['task__icontains'])

        if ordering is not None:
            qs = qs.order_by(ordering)

        count = 0
        for task_start_event in qs:
            # Create initial task data.
            task_data = {
                'related': {'job_event': reverse('api:job_event_detail', args=(task_start_event.pk,))},
                'type': 'job_event',
                'changed': task_start_event.changed,
                'changed_count': 0,
                'created': task_start_event.created,
                'failed': task_start_event.failed,
                'failed_count': 0,
                'host_count': 0,
                'id': task_start_event.id,
                'modified': task_start_event.modified,
                'name': 'Gathering Facts' if
                            task_start_event.event == 'playbook_on_setup' else
                            task_start_event.task,
                'reported_hosts': 0,
                'skipped_count': 0,
                'unreachable_count': 0,
                'successful_count': 0,
            }

            # Iterate over the data compiled for this child event, and
            # make appropriate changes to the task data.
            for child_data in data.get(task_start_event.id, []):
                if child_data['event'] == 'runner_on_failed':
                    task_data['failed'] = True
                    task_data['host_count'] += child_data['num']
                    task_data['reported_hosts'] += child_data['num']
                    task_data['failed_count'] += child_data['num']
                elif child_data['event'] == 'runner_on_ok':
                    task_data['host_count'] += child_data['num']
                    task_data['reported_hosts'] += child_data['num']
                    if child_data['changed']:
                        task_data['changed_count'] += child_data['num']
                        task_data['changed'] = True
                    else:
                        task_data['successful_count'] += child_data['num']
                elif child_data['event'] == 'runner_on_unreachable':
                    task_data['host_count'] += child_data['num']
                    task_data['unreachable_count'] += child_data['num']
                elif child_data['event'] == 'runner_on_skipped':
                    task_data['host_count'] += child_data['num']
                    task_data['reported_hosts'] += child_data['num']
                    task_data['skipped_count'] += child_data['num']
                elif child_data['event'] == 'runner_on_error':
                    task_data['host_count'] += child_data['num']
                    task_data['reported_hosts'] += child_data['num']
                    task_data['failed'] = True
                    task_data['failed_count'] += child_data['num']
                elif child_data['event'] == 'runner_on_no_hosts':
                    task_data['host_count'] += child_data['num']
            count += 1
            results.append(task_data)

        # Done; return the results and count.
        return (results, count, None)

class SystemJobList(ListCreateAPIView):

    model = SystemJob
    serializer_class = SystemJobListSerializer

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return super(SystemJobList, self).get(request, *args, **kwargs)


class SystemJobDetail(RetrieveDestroyAPIView):

    model = SystemJob
    serializer_class = SystemJobSerializer

class UnifiedJobTemplateList(ListAPIView):

    model = UnifiedJobTemplate
    serializer_class = UnifiedJobTemplateSerializer
    new_in_148 = True

class UnifiedJobList(ListAPIView):

    model = UnifiedJob
    serializer_class = UnifiedJobListSerializer
    new_in_148 = True

class UnifiedJobStdout(RetrieveAPIView):
    
    serializer_class = UnifiedJobStdoutSerializer
    renderer_classes = [BrowsableAPIRenderer, renderers.StaticHTMLRenderer,
                        PlainTextRenderer, AnsiTextRenderer,
                        renderers.JSONRenderer]
    filter_backends = ()
    new_in_148 = True

    def retrieve(self, request, *args, **kwargs):
        unified_job = self.get_object()
        if request.accepted_renderer.format in ('html', 'api', 'json'):
            scheme = request.QUERY_PARAMS.get('scheme', None)
            start_line = request.QUERY_PARAMS.get('start_line', 0)
            end_line = request.QUERY_PARAMS.get('end_line', None)
            if scheme not in SCHEME:
                scheme = 'ansi2html'
            dark_val = request.QUERY_PARAMS.get('dark', '')
            dark = bool(dark_val and dark_val[0].lower() in ('1', 't', 'y'))
            content_only = bool(request.accepted_renderer.format == 'api' or \
                                request.accepted_renderer.format == 'json')
            dark_bg = (content_only and dark) or (not content_only and (dark or not dark_val))
            conv = Ansi2HTMLConverter(scheme=scheme, dark_bg=dark_bg,
                                      title=get_view_name(self.__class__))
            content, start, end, absolute_end = unified_job.result_stdout_raw_limited(start_line, end_line)
            if content_only:
                headers = conv.produce_headers()
                body = conv.convert(content, full=False) # Escapes any HTML that may be in content.
                data = '\n'.join([headers, body])
                data = '<div class="nocode body_foreground body_background">%s</div>' % data
            else:
                data = conv.convert(content)
            # Fix ugly grey background used by default.
            data = data.replace('.body_background { background-color: #AAAAAA; }',
                                '.body_background { background-color: #f5f5f5; }')
            if request.accepted_renderer.format == 'api':
                return Response(mark_safe(data))
            if request.accepted_renderer.format == 'json':
                return Response({'range': {'start': start, 'end': end, 'absolute_end': absolute_end}, 'content': body})
            return Response(data)
        elif request.accepted_renderer.format == 'ansi':
            return Response(unified_job.result_stdout_raw)
        else:
            return super(UnifiedJobStdout, self).retrieve(request, *args, **kwargs)

class ProjectUpdateStdout(UnifiedJobStdout):

    model = ProjectUpdate

class InventoryUpdateStdout(UnifiedJobStdout):

    model = InventoryUpdate

class JobStdout(UnifiedJobStdout):

    model = Job

class ActivityStreamList(SimpleListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    new_in_145 = True

class ActivityStreamDetail(RetrieveAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    new_in_145 = True

# Create view functions for all of the class-based views to simplify inclusion
# in URL patterns and reverse URL lookups, converting CamelCase names to
# lowercase_with_underscore (e.g. MyView.as_view() becomes my_view).
this_module = sys.modules[__name__]
for attr, value in locals().items():
    if isinstance(value, type) and issubclass(value, APIView):
        name = camelcase_to_underscore(attr)
        view = value.as_view()
        setattr(this_module, name, view)
