
# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import os
import cgi
import datetime
import dateutil
import time
import socket
import sys
import errno
from base64 import b64encode
from collections import OrderedDict

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import FieldError
from django.db.models import Q, Count
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.core.servers.basehttp import FileWrapper
from django.http import HttpResponse

# Django REST Framework
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.parsers import FormParser
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
from social.backends.utils import load_backends

# AWX
from awx.main.task_engine import TaskSerializer, TASK_FILE, TEMPORARY_TASK_FILE
from awx.main.tasks import mongodb_control, send_notifications
from awx.main.access import get_user_queryset
from awx.main.ha import is_ha_environment
from awx.api.authentication import TaskAuthentication, TokenGetAuthentication
from awx.api.utils.decorators import paginated
from awx.api.generics import get_view_name
from awx.api.generics import * # noqa
from awx.api.license import feature_enabled, feature_exists, LicenseForbids
from awx.main.models import * # noqa
from awx.main.utils import * # noqa
from awx.api.permissions import * # noqa
from awx.api.renderers import * # noqa
from awx.api.serializers import * # noqa
from awx.main.utils import emit_websocket_notification
from awx.main.conf import tower_settings

def api_exception_handler(exc, context):
    '''
    Override default API exception handler to catch IntegrityError exceptions.
    '''
    if isinstance(exc, IntegrityError):
        exc = ParseError(exc.args[0])
    if isinstance(exc, FieldError):
        exc = ParseError(exc.args[0])
    return exception_handler(exc, context)

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

        data = OrderedDict()
        data['authtoken'] = reverse('api:auth_token_view')
        data['ping'] = reverse('api:api_v1_ping_view')
        data['config'] = reverse('api:api_v1_config_view')
        data['settings'] = reverse('api:settings_list')
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
        data['ad_hoc_commands'] = reverse('api:ad_hoc_command_list')
        data['system_job_templates'] = reverse('api:system_job_template_list')
        data['system_jobs'] = reverse('api:system_job_list')
        data['schedules'] = reverse('api:schedule_list')
        data['roles'] = reverse('api:role_list')
        data['notifiers'] = reverse('api:notifier_list')
        data['notifications'] = reverse('api:notification_list')
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
        license_data   = license_reader.from_database(show_key=request.user.is_superuser)

        pendo_state = tower_settings.PENDO_TRACKING_STATE if tower_settings.PENDO_TRACKING_STATE in ('off', 'anonymous', 'detailed') else 'off'

        data = dict(
            time_zone=settings.TIME_ZONE,
            license_info=license_data,
            version=get_awx_version(),
            ansible_version=get_ansible_version(),
            eula=render_to_string("eula.md"),
            analytics_status=pendo_state
        )

        # If LDAP is enabled, user_ldap_fields will return a list of field
        # names that are managed by LDAP and should be read-only for users with
        # a non-empty ldap_dn attribute.
        if getattr(settings, 'AUTH_LDAP_SERVER_URI', None) and feature_enabled('ldap'):
            user_ldap_fields = ['username', 'password']
            user_ldap_fields.extend(getattr(settings, 'AUTH_LDAP_USER_ATTR_MAP', {}).keys())
            user_ldap_fields.extend(getattr(settings, 'AUTH_LDAP_USER_FLAGS_BY_GROUP', {}).keys())
            data['user_ldap_fields'] = user_ldap_fields

        if request.user.is_superuser or request.user.admin_of_organizations.count():
            data.update(dict(
                project_base_dir = settings.PROJECTS_ROOT,
                project_local_paths = Project.get_local_path_choices(),
            ))

        return Response(data)

    def post(self, request):
        if not request.user.is_superuser:
            return Response(None, status=status.HTTP_404_NOT_FOUND)
        if not isinstance(request.data, dict):
            return Response({"error": "Invalid license data"}, status=status.HTTP_400_BAD_REQUEST)
        if "eula_accepted" not in request.data:
            return Response({"error": "Missing 'eula_accepted' property"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            eula_accepted = to_python_boolean(request.data["eula_accepted"])
        except ValueError:
            return Response({"error": "'eula_accepted' value is invalid"}, status=status.HTTP_400_BAD_REQUEST)

        if not eula_accepted:
            return Response({"error": "'eula_accepted' must be True"}, status=status.HTTP_400_BAD_REQUEST)
        request.data.pop("eula_accepted")
        try:
            data_actual = json.dumps(request.data)
        except Exception:
            # FIX: Log
            return Response({"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        license_reader = TaskSerializer()
        try:
            license_data = license_reader.from_string(data_actual)
        except Exception:
            # FIX: Log
            return Response({"error": "Invalid License"}, status=status.HTTP_400_BAD_REQUEST)

        # If the license is valid, write it to disk.
        if license_data['valid_key']:
            tower_settings.LICENSE = data_actual
            tower_settings.TOWER_URL_BASE = "{}://{}".format(request.scheme, request.get_host())
            return Response(license_data)

        return Response({"error": "Invalid license"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if not request.user.is_superuser:
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        # Remove license file
        has_error = None
        for fname in (TEMPORARY_TASK_FILE, TASK_FILE):
            try:
                os.remove(fname)
            except OSError, e:
                if e.errno != errno.ENOENT:
                    has_error = e.errno
                    break

        TowerSettings.objects.filter(key="LICENSE").delete()

        # Only stop mongod if license removal succeeded
        if has_error is None:
            mongodb_control.delay('stop')
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"error": "Failed to remove license (%s)" % has_error}, status=status.HTTP_400_BAD_REQUEST)

class DashboardView(APIView):

    view_name = "Dashboard"
    new_in_14 = True

    def get(self, request, format=None):
        ''' Show Dashboard Details '''
        data = OrderedDict()
        data['related'] = {'jobs_graph': reverse('api:dashboard_jobs_graph_view')}
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

class AuthView(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    new_in_240 = True

    def get(self, request):
        data = OrderedDict()
        err_backend, err_message = request.session.get('social_auth_error', (None, None))
        auth_backends = load_backends(settings.AUTHENTICATION_BACKENDS).items()
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
                    if err_backend == full_backend_name and err_message:
                        saml_backend_data['error'] = err_message
                    data[full_backend_name] = saml_backend_data
            else:
                if err_backend == name and err_message:
                    backend_data['error'] = err_message
                data[name] = backend_data
        return Response(data)

class AuthTokenView(APIView):

    authentication_classes = []
    permission_classes = (AllowAny,)
    serializer_class = AuthTokenSerializer
    model = AuthToken

    def get_serializer(self, *args, **kwargs):
        serializer = self.serializer_class(*args, **kwargs)
        # Override when called from browsable API to generate raw data form;
        # update serializer "validated" data to be displayed by the raw data
        # form.
        if hasattr(self, '_raw_data_form_marker'):
            # Always remove read only fields from serializer.
            for name, field in serializer.fields.items():
                if getattr(field, 'read_only', None):
                    del serializer.fields[name]
            serializer._data = self.update_raw_data(serializer.data)
        return serializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            request_hash = AuthToken.get_request_hash(self.request)
            try:
                token = AuthToken.objects.filter(user=serializer.validated_data['user'],
                                                 request_hash=request_hash,
                                                 expires__gt=now(),
                                                 reason='')[0]
                token.refresh()
            except IndexError:
                token = AuthToken.objects.create(user=serializer.validated_data['user'],
                                                 request_hash=request_hash)
                # Get user un-expired tokens that are not invalidated that are
                # over the configured limit.
                # Mark them as invalid and inform the user
                invalid_tokens = AuthToken.get_tokens_over_limit(serializer.validated_data['user'])
                for t in invalid_tokens:
                    # TODO: send socket notification
                    emit_websocket_notification('/socket.io/control',
                                                'limit_reached',
                                                dict(reason=force_text(AuthToken.reason_long('limit_reached'))),
                                                token_key=t.key)
                    t.invalidate(reason='limit_reached')

            # Note: This header is normally added in the middleware whenever an
            # auth token is included in the request header.
            headers = {
                'Auth-Token-Timeout': int(tower_settings.AUTH_TOKEN_EXPIRATION)
            }
            return Response({'token': token.key, 'expires': token.expires}, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrganizationList(ListCreateAPIView):

    model = Organization
    serializer_class = OrganizationSerializer

    def create(self, request, *args, **kwargs):
        """Create a new organzation.

        If there is already an organization and the license of the Tower
        instance does not permit multiple organizations, then raise
        LicenseForbids.
        """
        # Sanity check: If the multiple organizations feature is disallowed
        # by the license, then we are only willing to create this organization
        # if no organizations exist in the system.
        if (not feature_enabled('multiple_organizations') and
                self.model.objects.count() > 0):
            raise LicenseForbids('Your Tower license only permits a single '
                                 'organization to exist.')

        # Okay, create the organization as usual.
        return super(OrganizationList, self).create(request, *args, **kwargs)

class OrganizationDetail(RetrieveUpdateDestroyAPIView):

    model = Organization
    serializer_class = OrganizationSerializer

class OrganizationInventoriesList(SubListAPIView):

    model = Inventory
    serializer_class = InventorySerializer
    parent_model = Organization
    relationship = 'inventories'

class OrganizationUsersList(SubListCreateAttachDetachAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Organization
    relationship = 'member_role.members'

class OrganizationAdminsList(SubListCreateAttachDetachAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Organization
    relationship = 'admin_role.members'

class OrganizationProjectsList(SubListCreateAttachDetachAPIView):

    model = Project
    serializer_class = ProjectSerializer
    parent_model = Organization
    relationship = 'projects'

class OrganizationTeamsList(SubListCreateAttachDetachAPIView):

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

class OrganizationNotifiersList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = Organization
    relationship = 'notifiers'
    parent_key = 'organization'

class OrganizationNotifiersAnyList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = Organization
    relationship = 'notifiers_any'

class OrganizationNotifiersErrorList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = Organization
    relationship = 'notifiers_error'

class OrganizationNotifiersSuccessList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = Organization
    relationship = 'notifiers_success'

class OrganizationAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = Organization
    new_in_300 = True

class TeamList(ListCreateAPIView):

    model = Team
    serializer_class = TeamSerializer

class TeamDetail(RetrieveUpdateDestroyAPIView):

    model = Team
    serializer_class = TeamSerializer

class TeamUsersList(SubListCreateAttachDetachAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Team
    relationship = 'member_role.members'


class TeamRolesList(SubListCreateAttachDetachAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Team
    relationship='member_role.children'

    def get_queryset(self):
        team = Team.objects.get(pk=self.kwargs['pk'])
        return team.member_role.children.filter(id__in=Role.visible_roles(self.request.user))

    # XXX: Need to enforce permissions
    def post(self, request, *args, **kwargs):
        # Forbid implicit role creation here
        sub_id = request.data.get('id', None)
        if not sub_id:
            data = dict(msg='Role "id" field is missing')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return super(type(self), self).post(request, *args, **kwargs)

class TeamProjectsList(SubListCreateAttachDetachAPIView):

    model = Project
    serializer_class = ProjectSerializer
    parent_model = Team
    relationship = 'projects'

class TeamCredentialsList(SubListCreateAttachDetachAPIView):

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(team=parent) |
                         Q(project__in=parent.projects.all()) |
                         Q(credential__in=parent.credentials.all()) |
                         Q(permission__in=parent.permissions.all()))

class TeamAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = Team
    new_in_300 = True

class ProjectList(ListCreateAPIView):

    model = Project
    serializer_class = ProjectSerializer

    def get(self, request, *args, **kwargs):
        # Not optimal, but make sure the project status and last_updated fields
        # are up to date here...
        projects_qs = Project.objects
        projects_qs = projects_qs.select_related('current_job', 'last_job')
        for project in projects_qs:
            project._set_status_and_last_job_run()
        return super(ProjectList, self).get(request, *args, **kwargs)

class ProjectDetail(RetrieveUpdateDestroyAPIView):

    model = Project
    serializer_class = ProjectSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = request.user.can_access(Project, 'delete', obj)
        if not can_delete:
            raise PermissionDenied("Cannot delete project")
        for pu in obj.project_updates.filter(status__in=['new', 'pending', 'waiting', 'running']):
            pu.cancel()
        return super(ProjectDetail, self).destroy(request, *args, **kwargs)

class ProjectPlaybooks(RetrieveAPIView):

    model = Project
    serializer_class = ProjectPlaybooksSerializer

class ProjectTeamsList(SubListCreateAttachDetachAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = Project
    relationship = 'teams'

class ProjectSchedulesList(SubListCreateAttachDetachAPIView):

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        if parent is None:
            return qs
        elif parent.credential is None:
            return qs.filter(project=parent)
        return qs.filter(Q(project=parent) | Q(credential__in=parent.credential))

class ProjectNotifiersAnyList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = Project
    relationship = 'notifiers_any'

class ProjectNotifiersErrorList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = Project
    relationship = 'notifiers_error'

class ProjectNotifiersSuccessList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = Project
    relationship = 'notifiers_success'

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
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class ProjectUpdateNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = Project
    relationship = 'notifications'

class ProjectAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = Project
    new_in_300 = True

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


class UserRolesList(SubListCreateAttachDetachAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = User
    relationship='roles'
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        #u = User.objects.get(pk=self.kwargs['pk'])
        return Role.visible_roles(self.request.user).filter(members__in=[int(self.kwargs['pk']), ])

    def post(self, request, *args, **kwargs):
        # Forbid implicit role creation here
        sub_id = request.data.get('id', None)
        if not sub_id:
            data = dict(msg='Role "id" field is missing')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return super(type(self), self).post(request, *args, **kwargs)

    def check_parent_access(self, parent=None):
        # We hide roles that shouldn't be seen in our queryset
        return True



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

class UserCredentialsList(SubListCreateAttachDetachAPIView):

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

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
        if can_change and not can_admin:
            admin_only_edit_fields = ('last_name', 'first_name', 'username',
                                      'is_active', 'is_superuser')
            changed = {}
            for field in admin_only_edit_fields:
                left = getattr(obj, field, None)
                right = request.data.get(field, None)
                if left is not None and right is not None and left != right:
                    changed[field] = (left, right)
            if changed:
                raise PermissionDenied('Cannot change %s' % ', '.join(changed.keys()))

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = request.user.can_access(User, 'delete', obj)
        if not can_delete:
            raise PermissionDenied('Cannot delete user')
        return super(UserDetail, self).destroy(request, *args, **kwargs)

class UserAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = User
    new_in_300 = True

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

class CredentialAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = Credential
    new_in_300 = True

class InventoryScriptList(ListCreateAPIView):

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer

class InventoryScriptDetail(RetrieveUpdateDestroyAPIView):

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        can_delete = request.user.can_access(self.model, 'delete', instance)
        if not can_delete:
            raise PermissionDenied("Cannot delete inventory script")
        for inv_src in InventorySource.objects.filter(source_script=instance):
            inv_src.source_script = None
            inv_src.save()
        return super(InventoryScriptDetail, self).destroy(request, *args, **kwargs)

class InventoryList(ListCreateAPIView):

    model = Inventory
    serializer_class = InventorySerializer

class InventoryDetail(RetrieveUpdateDestroyAPIView):

    model = Inventory
    serializer_class = InventoryDetailSerializer

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(inventory=parent) | Q(host__in=parent.hosts.all()) | Q(group__in=parent.groups.all()))

class InventoryAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = Inventory
    new_in_300 = True

class InventoryJobTemplateList(SubListAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    parent_model = Inventory
    relationship = 'jobtemplates'
    new_in_300 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(inventory=parent)

class InventoryScanJobTemplateList(SubListAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    parent_model = Inventory
    relationship = 'jobtemplates'
    new_in_220 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(job_type=PERM_INVENTORY_SCAN, inventory=parent)

class HostList(ListCreateAPIView):

    model = Host
    serializer_class = HostSerializer

class HostDetail(RetrieveUpdateDestroyAPIView):

    model = Host
    serializer_class = HostSerializer

class InventoryHostsList(SubListCreateAttachDetachAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = Inventory
    relationship = 'hosts'
    parent_key = 'inventory'

class HostGroupsList(SubListCreateAttachDetachAPIView):
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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(host=parent) | Q(inventory=parent.inventory))

class SystemTrackingEnforcementMixin(APIView):
    '''
    Use check_permissions instead of initial() because it's in the OPTION's path as well
    '''
    def check_permissions(self, request):
        if not feature_enabled("system_tracking"):
            raise LicenseForbids("Your license does not permit use "
                                 "of system tracking.")
        return super(SystemTrackingEnforcementMixin, self).check_permissions(request)

class HostFactVersionsList(ListAPIView, ParentMixin, SystemTrackingEnforcementMixin):

    model = Fact
    serializer_class = FactVersionSerializer
    parent_model = Host
    new_in_220 = True

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

class HostFactCompareView(SubDetailAPIView, SystemTrackingEnforcementMixin):

    model = Fact
    new_in_220 = True
    parent_model = Host
    serializer_class = FactSerializer

    def retrieve(self, request, *args, **kwargs):
        datetime_spec = request.query_params.get('datetime', None)
        module_spec = request.query_params.get('module', "ansible")
        datetime_actual = dateutil.parser.parse(datetime_spec) if datetime_spec is not None else now()

        host_obj = self.get_parent_object()

        fact_entry = Fact.get_host_fact(host_obj.id, module_spec, datetime_actual)
        if not fact_entry:
            return Response({'detail': 'Fact not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.serializer_class(instance=fact_entry).data)

class GroupList(ListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer

class GroupChildrenList(SubListCreateAttachDetachAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Group
    relationship = 'children'

    def update_raw_data(self, data):
        data.pop('inventory', None)
        return super(GroupChildrenList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject parent group inventory ID into new group data.
        data = request.data
        # HACK: Make request data mutable.
        if getattr(data, '_mutable', None) is False:
            data._mutable = True
        data['inventory'] = self.get_parent_object().inventory_id
        return super(GroupChildrenList, self).create(request, *args, **kwargs)

    def unattach(self, request, *args, **kwargs):
        sub_id = request.data.get('id', None)
        if sub_id is not None:
            return super(GroupChildrenList, self).unattach(request, *args, **kwargs)
        parent = self.get_parent_object()
        parent.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _unattach(self, request, *args, **kwargs): # FIXME: Disabled for now for UI support.
        '''
        Special case for disassociating a child group from the parent. If the
        child group has no more parents, then automatically mark it inactive.
        '''
        sub_id = request.data.get('id', None)
        if not sub_id:
            data = dict(msg='"id" is required to disassociate')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        parent = self.get_parent_object()
        # TODO: flake8 warns, pending removal if unneeded
        # parent_key = getattr(self, 'parent_key', None)
        relationship = getattr(parent, self.relationship)
        sub = get_object_or_400(self.model, pk=sub_id)

        if not request.user.can_access(self.parent_model, 'unattach', parent,
                                       sub, self.relationship):
            raise PermissionDenied()

        if sub.parents.exclude(pk=parent.pk).count() == 0:
            sub.delete()
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

class GroupHostsList(SubListCreateAttachDetachAPIView):
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
        existing_hosts = Host.objects.filter(inventory=parent_group.inventory, name=request.data['name'])
        if existing_hosts.count() > 0 and ('variables' not in request.data or
                                           request.data['variables'] == '' or
                                           request.data['variables'] == '{}' or
                                           request.data['variables'] == '---'):
            request.data['id'] = existing_hosts[0].id
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
        qs = self.request.user.get_queryset(self.model).distinct() # need distinct for '&' operator
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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

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
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        obj.delete_recursive()
        return Response(status=status.HTTP_204_NO_CONTENT)

class GroupAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = Group
    new_in_300 = True


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
    authentication_classes = [TaskAuthentication] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (TaskPermission,)
    filter_backends = ()

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        hostname = request.query_params.get('host', '')
        hostvars = bool(request.query_params.get('hostvars', ''))
        show_all = bool(request.query_params.get('all', ''))
        if show_all:
            hosts_q = dict()
        else:
            hosts_q = dict(enabled=True)
        if hostname:
            host = get_object_or_404(obj.hosts, name=hostname, **hosts_q)
            data = host.variables_dict
        else:
            data = OrderedDict()
            if obj.variables_dict:
                all_group = data.setdefault('all', OrderedDict())
                all_group['vars'] = obj.variables_dict

            # Add hosts without a group to the all group.
            groupless_hosts_qs = obj.hosts.filter(groups__isnull=True, **hosts_q).order_by('name')
            groupless_hosts = list(groupless_hosts_qs.values_list('name', flat=True))
            if groupless_hosts:
                all_group = data.setdefault('all', OrderedDict())
                all_group['hosts'] = groupless_hosts

            # Build in-memory mapping of groups and their hosts.
            group_hosts_kw = dict(group__inventory_id=obj.id, host__inventory_id=obj.id)
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
                from_group__inventory_id=obj.id,
                to_group__inventory_id=obj.id,
            )
            group_parents_qs = group_parents_qs.order_by('from_group__name')
            group_parents_qs = group_parents_qs.values_list('from_group_id', 'from_group__name', 'to_group_id')
            group_children_map = {}
            for from_group_id, from_group_name, to_group_id in group_parents_qs:
                group_children = group_children_map.setdefault(to_group_id, [])
                group_children.append(from_group_name)

            # Now use in-memory maps to build up group info.
            for group in obj.groups.all():
                group_info = OrderedDict()
                group_info['hosts'] = group_hosts_map.get(group.id, [])
                group_info['children'] = group_children_map.get(group.id, [])
                group_info['vars'] = group.variables_dict
                data[group.name] = group_info

            if hostvars:
                data.setdefault('_meta', OrderedDict())
                data['_meta'].setdefault('hostvars', OrderedDict())
                for host in obj.hosts.filter(**hosts_q):
                    data['_meta']['hostvars'][host.name] = host.variables_dict

            # workaround for Ansible inventory bug (github #3687), localhost
            # must be explicitly listed in the all group for dynamic inventory
            # scripts to pick it up.
            localhost_names = ('localhost', '127.0.0.1', '::1')
            localhosts_qs = obj.hosts.filter(name__in=localhost_names, **hosts_q)
            localhosts = list(localhosts_qs.values_list('name', flat=True))
            if localhosts:
                all_group = data.setdefault('all', OrderedDict())
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
        group_children_map = inventory.get_group_children_map()
        root_group_pks = inventory.root_groups.order_by('name').values_list('pk', flat=True)
        groups_qs = inventory.groups
        groups_qs = groups_qs.select_related('inventory')
        groups_qs = groups_qs.prefetch_related('inventory_source')
        all_group_data = GroupSerializer(groups_qs, many=True).data
        all_group_data_map = dict((x['id'], x) for x in all_group_data)
        tree_data = [all_group_data_map[x] for x in root_group_pks]
        for group_data in tree_data:
            self._populate_group_children(group_data, all_group_data_map,
                                          group_children_map)
        return Response(tree_data)

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
        obj = self.get_object()
        can_delete = request.user.can_access(InventorySource, 'delete', obj)
        if not can_delete:
            raise PermissionDenied("Cannot delete inventory source")
        for pu in obj.inventory_updates.filter(status__in=['new', 'pending', 'waiting', 'running']):
            pu.cancel()
        return super(InventorySourceDetail, self).destroy(request, *args, **kwargs)

class InventorySourceSchedulesList(SubListCreateAttachDetachAPIView):

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

class InventorySourceNotifiersAnyList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = InventorySource
    relationship = 'notifiers_any'

class InventorySourceNotifiersErrorList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = InventorySource
    relationship = 'notifiers_error'

class InventorySourceNotifiersSuccessList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = InventorySource
    relationship = 'notifiers_success'

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
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class InventoryUpdateNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = InventoryUpdate
    relationship = 'notifications'

class JobTemplateList(ListCreateAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    always_allow_superuser = False

class JobTemplateDetail(RetrieveUpdateDestroyAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    always_allow_superuser = False

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = request.user.can_access(JobTemplate, 'delete', obj)
        if not can_delete:
            raise PermissionDenied("Cannot delete job template")
        for pu in obj.jobs.filter(status__in=['new', 'pending', 'waiting', 'running']):
            pu.cancel()
        return super(JobTemplateDetail, self).destroy(request, *args, **kwargs)


class JobTemplateLaunch(RetrieveAPIView, GenericAPIView):

    model = JobTemplate
    serializer_class = JobLaunchSerializer
    is_job_start = True
    always_allow_superuser = False

    def update_raw_data(self, data):
        obj = self.get_object()
        extra_vars = data.get('extra_vars') or {}
        if obj:
            for p in obj.passwords_needed_to_start:
                data[p] = u''
            if obj.credential:
                data.pop('credential', None)
            else:
                data['credential'] = None
            for v in obj.variables_needed_to_start:
                extra_vars.setdefault(v, u'')
        data['extra_vars'] = extra_vars
        return data

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()

        if 'credential' not in request.data and 'credential_id' in request.data:
            request.data['credential'] = request.data['credential_id']

        passwords = {}
        serializer = self.serializer_class(instance=obj, data=request.data, context={'obj': obj, 'data': request.data, 'passwords': passwords})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # At this point, a credential is gauranteed to exist at serializer.instance.credential
        if not request.user.can_access(Credential, 'read', serializer.instance.credential):
            raise PermissionDenied()

        kv = {
            'credential': serializer.instance.credential.pk,
        }
        if 'extra_vars' in request.data:
            kv['extra_vars'] = request.data['extra_vars']
        kv.update(passwords)

        new_job = obj.create_unified_job(**kv)
        result = new_job.signal_start(**kv)
        if not result:
            data = dict(passwords_needed_to_start=new_job.passwords_needed_to_start)
            new_job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = dict(job=new_job.id)
            return Response(data, status=status.HTTP_202_ACCEPTED)

class JobTemplateSchedulesList(SubListCreateAttachDetachAPIView):

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
    serializer_class = EmptySerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.survey_enabled:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(obj.survey_spec)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        # Sanity check: Are surveys available on this license?
        # If not, do not allow them to be used.
        if not feature_enabled('surveys'):
            raise LicenseForbids('Your license does not allow '
                                 'adding surveys.')

        if not request.user.can_access(self.model, 'change', obj, None):
            raise PermissionDenied()
        try:
            obj.survey_spec = json.dumps(request.data)
        except ValueError:
            # TODO: Log
            return Response(dict(error="Invalid JSON when parsing survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if "name" not in obj.survey_spec:
            return Response(dict(error="'name' missing from survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if "description" not in obj.survey_spec:
            return Response(dict(error="'description' missing from survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if "spec" not in obj.survey_spec:
            return Response(dict(error="'spec' missing from survey spec"), status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(obj.survey_spec["spec"], list):
            return Response(dict(error="'spec' must be a list of items"), status=status.HTTP_400_BAD_REQUEST)
        if len(obj.survey_spec["spec"]) < 1:
            return Response(dict(error="'spec' doesn't contain any items"), status=status.HTTP_400_BAD_REQUEST)
        idx = 0
        for survey_item in obj.survey_spec["spec"]:
            if not isinstance(survey_item, dict):
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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

class JobTemplateNotifiersAnyList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = JobTemplate
    relationship = 'notifiers_any'

class JobTemplateNotifiersErrorList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = JobTemplate
    relationship = 'notifiers_error'

class JobTemplateNotifiersSuccessList(SubListCreateAttachDetachAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    parent_model = JobTemplate
    relationship = 'notifiers_success'

class JobTemplateCallback(GenericAPIView):

    model = JobTemplate
    permission_classes = (JobTemplateCallbackPermission,)
    serializer_class = EmptySerializer
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
        qs = obj.inventory.hosts
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
        extra_vars = None
        if request.content_type == "application/json":
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
        kv = {"inventory_sources_already_updated": inventory_sources_already_updated}
        if extra_vars is not None:
            kv['extra_vars'] = extra_vars
        result = job.signal_start(**kv)
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

class JobTemplateAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    resource_model = JobTemplate
    new_in_300 = True

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
    serializer_class = EmptySerializer

    def get(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()

        new_job = obj.create_unified_job(**request.data)
        new_job.signal_start(**request.data)
        data = dict(system_job=new_job.id)
        return Response(data, status=status.HTTP_202_ACCEPTED)

class SystemJobTemplateSchedulesList(SubListCreateAttachDetachAPIView):

    view_name = "System Job Template Schedules"

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

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

class JobStart(GenericAPIView):

    model = Job
    serializer_class = EmptySerializer
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
    serializer_class = JobCancelSerializer
    is_job_cancel = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)

class JobRelaunch(RetrieveAPIView, GenericAPIView):

    model = Job
    serializer_class = JobRelaunchSerializer
    is_job_start = True

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(JobRelaunch, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()

        # Note: is_valid() may modify request.data
        # It will remove any key/value pair who's key is not in the 'passwords_needed_to_start' list
        serializer = self.serializer_class(data=request.data, context={'obj': obj, 'data': request.data})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        obj.launch_type = 'relaunch'
        new_job = obj.copy()
        result = new_job.signal_start(**request.data)
        if not result:
            data = dict(passwords_needed_to_start=new_job.passwords_needed_to_start)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = JobSerializer(new_job).data
            # Add job key to match what old relaunch returned.
            data['job'] = new_job.id
            headers = {'Location': new_job.get_absolute_url()}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)

class JobNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = Job
    relationship = 'notifications'

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
    authentication_classes = [TaskAuthentication] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (TaskPermission,)

    # Post allowed for job event callback only.
    def post(self, request, *args, **kwargs):
        parent_obj = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        data = request.data.copy()
        data['job'] = parent_obj.pk
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.instance = serializer.save()
            headers = {'Location': serializer.data['url']}
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobJobPlaysList(BaseJobEventsList):

    parent_model = Job
    view_name = 'Job Plays List'
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

        if "id__in" in request.query_params:
            qs = qs.filter(id__in=[int(filter_id) for filter_id in request.query_params["id__in"].split(",")])
        elif "id__gt" in request.query_params:
            qs = qs.filter(id__gt=request.query_params['id__gt'])
        elif "id__lt" in request.query_params:
            qs = qs.filter(id__lt=request.query_params['id__lt'])
        if "failed" in request.query_params:
            qs = qs.filter(failed=(request.query_params['failed'].lower() == 'true'))
        if "play__icontains" in request.query_params:
            qs = qs.filter(play__icontains=request.query_params['play__icontains'])

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
                if not change_aggregate['changed']:
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

        if 'event_id' not in request.query_params:
            return ({'detail': '"event_id" not provided'}, -1, status.HTTP_400_BAD_REQUEST)

        parent_task = job.job_events.filter(pk=int(request.query_params.get('event_id', -1)))
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

        if "id__in" in request.query_params:
            qs = qs.filter(id__in=[int(filter_id) for filter_id in request.query_params["id__in"].split(",")])
        elif "id__gt" in request.query_params:
            qs = qs.filter(id__gt=request.query_params['id__gt'])
        elif "id__lt" in request.query_params:
            qs = qs.filter(id__lt=request.query_params['id__lt'])
        if "failed" in request.query_params:
            qs = qs.filter(failed=(request.query_params['failed'].lower() == 'true'))
        if "task__icontains" in request.query_params:
            qs = qs.filter(task__icontains=request.query_params['task__icontains'])

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
                'name': 'Gathering Facts' if task_start_event.event == 'playbook_on_setup' else task_start_event.task,
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


class AdHocCommandList(ListCreateAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandListSerializer
    new_in_220 = True
    always_allow_superuser = False

    @csrf_exempt
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


class AdHocCommandDetail(RetrieveDestroyAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandSerializer
    new_in_220 = True


class AdHocCommandCancel(RetrieveAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandCancelSerializer
    is_job_cancel = True
    new_in_220 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class AdHocCommandRelaunch(GenericAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandRelaunchSerializer
    is_job_start = True
    new_in_220 = True

    # FIXME: Figure out why OPTIONS request still shows all fields.

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(AdHocCommandRelaunch, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data = dict(passwords_needed_to_start=obj.passwords_needed_to_start)
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'start', obj):
            raise PermissionDenied()

        # Re-validate ad hoc command against serializer to check if module is
        # still allowed.
        data = {}
        for field in ('job_type', 'inventory_id', 'limit', 'credential_id',
                      'module_name', 'module_args', 'forks', 'verbosity',
                      'become_enabled'):
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
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = AdHocCommandSerializer(new_ad_hoc_command).data
            # Add ad_hoc_command key to match what was previously returned.
            data['ad_hoc_command'] = new_ad_hoc_command.id
            headers = {'Location': new_ad_hoc_command.get_absolute_url()}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class AdHocCommandEventList(ListAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    new_in_220 = True


class AdHocCommandEventDetail(RetrieveAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    new_in_220 = True


class BaseAdHocCommandEventsList(SubListAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'ad_hoc_command_events'
    view_name = 'Ad Hoc Command Events List'
    new_in_220 = True


class HostAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = Host
    new_in_220 = True

#class GroupJobEventsList(BaseJobEventsList):
#    parent_model = Group


class AdHocCommandAdHocCommandEventsList(BaseAdHocCommandEventsList):

    parent_model = AdHocCommand
    authentication_classes = [TaskAuthentication] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (TaskPermission,)
    new_in_220 = True

    # Post allowed for ad hoc event callback only.
    def post(self, request, *args, **kwargs):
        if request.user:
            raise PermissionDenied()
        parent_obj = get_object_or_404(self.parent_model, pk=self.kwargs['pk'])
        data = request.data.copy()
        data['ad_hoc_command'] = parent_obj
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            self.instance = serializer.save()
            headers = {'Location': serializer.data['url']}
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdHocCommandActivityStreamList(SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = AdHocCommand
    relationship = 'activitystream_set'
    new_in_220 = True

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)


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

class SystemJobCancel(RetrieveAPIView):

    model = SystemJob
    serializer_class = SystemJobCancelSerializer
    is_job_cancel = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class UnifiedJobTemplateList(ListAPIView):

    model = UnifiedJobTemplate
    serializer_class = UnifiedJobTemplateSerializer
    new_in_148 = True

class UnifiedJobList(ListAPIView):

    model = UnifiedJob
    serializer_class = UnifiedJobListSerializer
    new_in_148 = True

class UnifiedJobStdout(RetrieveAPIView):

    authentication_classes = [TokenGetAuthentication] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    serializer_class = UnifiedJobStdoutSerializer
    renderer_classes = [BrowsableAPIRenderer, renderers.StaticHTMLRenderer,
                        PlainTextRenderer, AnsiTextRenderer,
                        renderers.JSONRenderer, DownloadTextRenderer]
    filter_backends = ()
    new_in_148 = True

    def retrieve(self, request, *args, **kwargs):
        unified_job = self.get_object()
        obj_size = unified_job.result_stdout_size
        if request.accepted_renderer.format != 'txt_download' and obj_size > tower_settings.STDOUT_MAX_BYTES_DISPLAY:
            response_message = "Standard Output too large to display (%d bytes), only download supported for sizes over %d bytes" % (obj_size,
                                                                                                                                     tower_settings.STDOUT_MAX_BYTES_DISPLAY)
            if request.accepted_renderer.format == 'json':
                return Response({'range': {'start': 0, 'end': 1, 'absolute_end': 1}, 'content': response_message})
            else:
                return Response(response_message)

        if request.accepted_renderer.format in ('html', 'api', 'json'):
            content_format = request.query_params.get('content_format', 'html')
            content_encoding = request.query_params.get('content_encoding', None)
            start_line = request.query_params.get('start_line', 0)
            end_line = request.query_params.get('end_line', None)
            dark_val = request.query_params.get('dark', '')
            dark = bool(dark_val and dark_val[0].lower() in ('1', 't', 'y'))
            content_only = bool(request.accepted_renderer.format in ('api', 'json'))
            dark_bg = (content_only and dark) or (not content_only and (dark or not dark_val))
            content, start, end, absolute_end = unified_job.result_stdout_raw_limited(start_line, end_line)

            body = ansiconv.to_html(cgi.escape(content))
            context = {
                'title': get_view_name(self.__class__),
                'body': mark_safe(body),
                'dark': dark_bg,
                'content_only': content_only,
            }
            data = render_to_string('api/stdout.html', context).strip()

            if request.accepted_renderer.format == 'api':
                return Response(mark_safe(data))
            if request.accepted_renderer.format == 'json':
                if content_encoding == 'base64' and content_format == 'ansi':
                    return Response({'range': {'start': start, 'end': end, 'absolute_end': absolute_end}, 'content': b64encode(content)})
                elif content_format == 'html':
                    return Response({'range': {'start': start, 'end': end, 'absolute_end': absolute_end}, 'content': body})
            return Response(data)
        elif request.accepted_renderer.format == 'ansi':
            return Response(unified_job.result_stdout_raw)
        elif request.accepted_renderer.format == 'txt_download':
            try:
                content_fd = open(unified_job.result_stdout_file, 'r')
                response = HttpResponse(FileWrapper(content_fd), content_type='text/plain')
                response["Content-Disposition"] = 'attachment; filename="job_%s.txt"' % str(unified_job.id)
                return response
            except Exception, e:
                return Response({"error": "Error generating stdout download file: %s" % str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif request.accepted_renderer.format == 'txt':
            return Response(unified_job.result_stdout)
        else:
            return super(UnifiedJobStdout, self).retrieve(request, *args, **kwargs)

class ProjectUpdateStdout(UnifiedJobStdout):

    model = ProjectUpdate

class InventoryUpdateStdout(UnifiedJobStdout):

    model = InventoryUpdate

class JobStdout(UnifiedJobStdout):

    model = Job

class AdHocCommandStdout(UnifiedJobStdout):

    model = AdHocCommand
    new_in_220 = True

class NotifierList(ListCreateAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    new_in_300 = True

class NotifierDetail(RetrieveUpdateDestroyAPIView):

    model = Notifier
    serializer_class = NotifierSerializer
    new_in_300 = True

class NotifierTest(GenericAPIView):

    view_name = 'Notifier Test'
    model = Notifier
    serializer_class = EmptySerializer
    new_in_300 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        notification = obj.generate_notification("Tower Notification Test {} {}".format(obj.id, tower_settings.TOWER_URL_BASE),
                                                 {"body": "Ansible Tower Test Notification {} {}".format(obj.id, tower_settings.TOWER_URL_BASE)})
        if not notification:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        else:
            send_notifications.delay([notification.id])
            headers = {'Location': notification.get_absolute_url()}
            return Response({"notification": notification.id},
                            headers=headers,
                            status=status.HTTP_202_ACCEPTED)

class NotifierNotificationList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = Notifier
    relationship = 'notifications'
    parent_key = 'notifier'

class NotificationList(ListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    new_in_300 = True

class NotificationDetail(RetrieveAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    new_in_300 = True

class ActivityStreamList(SimpleListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    new_in_145 = True

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)


class ActivityStreamDetail(RetrieveAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    new_in_145 = True

    def get(self, request, *args, **kwargs):
        # Sanity check: Does this license allow activity streams?
        # If not, forbid this request.
        if not feature_enabled('activity_streams'):
            raise LicenseForbids('Your license does not allow use of '
                                 'the activity stream.')

        # Okay, let it through.
        return super(type(self), self).get(request, *args, **kwargs)

class SettingsList(ListCreateAPIView):

    model = TowerSettings
    serializer_class = TowerSettingsSerializer
    authentication_classes = [TokenGetAuthentication] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    new_in_300 = True
    filter_backends = ()

    def get_queryset(self):
        class SettingsIntermediary(object):
            def __init__(self, key, description, category, value,
                         value_type, user=None):
                self.key = key
                self.description = description
                self.category = category
                self.value = value
                self.value_type = value_type
                self.user = user

        if not self.request.user.is_superuser:
            # NOTE: Shortcutting the rbac class due to the merging of the settings manifest and the database
            #       we'll need to extend this more in the future when we have user settings
            return []
        all_defined_settings = {}
        for s in TowerSettings.objects.all():
            all_defined_settings[s.key] = SettingsIntermediary(s.key,
                                                               s.description,
                                                               s.category,
                                                               s.value_converted,
                                                               s.value_type,
                                                               s.user)
        manifest_settings = settings.TOWER_SETTINGS_MANIFEST
        settings_actual = []
        for settings_key in manifest_settings:
            if settings_key in all_defined_settings:
                settings_actual.append(all_defined_settings[settings_key])
            else:
                m_entry = manifest_settings[settings_key]
                settings_actual.append(SettingsIntermediary(settings_key,
                                                            m_entry['description'],
                                                            m_entry['category'],
                                                            m_entry['default'],
                                                            m_entry['type']))
        return settings_actual

    def delete(self, request, *args, **kwargs):
        if not request.user.can_access(self.model, 'delete', None):
            raise PermissionDenied()
        TowerSettings.objects.all().delete()
        return Response()

class SettingsReset(APIView):

    view_name = "Reset a settings value"
    new_in_300 = True

    def post(self, request):
        # NOTE: Extend more with user settings
        if not request.user.can_access(TowerSettings, 'delete', None):
            raise PermissionDenied()
        settings_key = request.data.get('key', None)
        if settings_key is not None:
            TowerSettings.objects.filter(key=settings_key).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleList(ListAPIView):

    model = Role
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)
    new_in_300 = True

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Role.objects
        return Role.visible_roles(self.request.user)


class RoleDetail(RetrieveAPIView):

    model = Role
    serializer_class = RoleSerializer
    permission_classes = (IsAuthenticated,)
    new_in_300 = True


class RoleUsersList(SubListCreateAttachDetachAPIView):

    model = User
    serializer_class = UserSerializer
    parent_model = Role
    relationship = 'members'
    permission_classes = (IsAuthenticated,)
    new_in_300 = True

    def get_queryset(self):
        # XXX: Access control
        role = Role.objects.get(pk=self.kwargs['pk'])
        return role.members

    def post(self, request, *args, **kwargs):
        # Forbid implicit role creation here
        sub_id = request.data.get('id', None)
        if not sub_id:
            data = dict(msg='Role "id" field is missing')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return super(type(self), self).post(request, *args, **kwargs)


class RoleTeamsList(ListAPIView):

    model = Team
    serializer_class = TeamSerializer
    parent_model = Role
    relationship = 'member_role.parents'
    permission_classes = (IsAuthenticated,)
    new_in_300 = True

    def get_queryset(self):
        # TODO: Check
        role = Role.objects.get(pk=self.kwargs['pk'])
        return Team.objects.filter(member_role__children__in=[role])

    def post(self, request, pk, *args, **kwargs):
        # Forbid implicit role creation here
        sub_id = request.data.get('id', None)
        if not sub_id:
            data = dict(msg='Role "id" field is missing')
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        # XXX: Need to pull in can_attach and can_unattach kinda code from SubListCreateAttachDetachAPIView
        role = Role.objects.get(pk=self.kwargs['pk'])
        team = Team.objects.get(pk=sub_id)
        if request.data.get('disassociate', None):
            team.member_role.children.remove(role)
        else:
            team.member_role.children.add(role)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # XXX attach/detach needs to ensure we have the appropriate perms


class RoleParentsList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Role
    relationship = 'parents'
    permission_classes = (IsAuthenticated,)
    new_in_300 = True

    def get_queryset(self):
        # XXX: This should be the intersection between the roles of the user
        # and the roles that the requesting user has access to see
        role = Role.objects.get(pk=self.kwargs['pk'])
        return role.parents

class RoleChildrenList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Role
    relationship = 'children'
    permission_classes = (IsAuthenticated,)
    new_in_300 = True

    def get_queryset(self):
        # XXX: This should be the intersection between the roles of the user
        # and the roles that the requesting user has access to see
        role = Role.objects.get(pk=self.kwargs['pk'])
        return role.children




# Create view functions for all of the class-based views to simplify inclusion
# in URL patterns and reverse URL lookups, converting CamelCase names to
# lowercase_with_underscore (e.g. MyView.as_view() becomes my_view).
this_module = sys.modules[__name__]
for attr, value in locals().items():
    if isinstance(value, type) and issubclass(value, APIView):
        name = camelcase_to_underscore(attr)
        view = value.as_view()
        setattr(this_module, name, view)
