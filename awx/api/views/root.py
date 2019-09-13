# Copyright (c) 2018 Ansible, Inc.
# All Rights Reserved.

import logging
import operator
import json
from collections import OrderedDict

from django.conf import settings
from django.utils.encoding import smart_text
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

import requests

from awx.api.generics import APIView
from awx.main.ha import is_ha_environment
from awx.main.utils import (
    get_awx_version,
    get_ansible_version,
    get_custom_venv_choices,
    to_python_boolean,
)
from awx.api.versioning import reverse, drf_reverse
from awx.conf.license import get_license
from awx.main.constants import PRIVILEGE_ESCALATION_METHODS
from awx.main.models import (
    Project,
    Organization,
    Instance,
    InstanceGroup,
    JobTemplate,
)

logger = logging.getLogger('awx.api.views.root')


class ApiRootView(APIView):

    permission_classes = (AllowAny,)
    name = _('REST API')
    versioning_class = None
    swagger_topic = 'Versioning'

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, format=None):
        ''' List supported API versions '''

        v2 = reverse('api:api_v2_root_view', kwargs={'version': 'v2'})
        data = OrderedDict()
        data['description'] = _('AWX REST API')
        data['current_version'] = v2
        data['available_versions'] = dict(v2 = v2)
        data['oauth2'] = drf_reverse('api:oauth_authorization_root_view')
        data['custom_logo'] = settings.CUSTOM_LOGO
        data['custom_login_info'] = settings.CUSTOM_LOGIN_INFO
        return Response(data)


class ApiOAuthAuthorizationRootView(APIView):

    permission_classes = (AllowAny,)
    name = _("API OAuth 2 Authorization Root")
    versioning_class = None
    swagger_topic = 'Authentication'

    def get(self, request, format=None):
        data = OrderedDict()
        data['authorize'] = drf_reverse('api:authorize')
        data['token'] = drf_reverse('api:token')
        data['revoke_token'] = drf_reverse('api:revoke-token')
        return Response(data)


class ApiVersionRootView(APIView):

    permission_classes = (AllowAny,)
    swagger_topic = 'Versioning'

    def get(self, request, format=None):
        ''' List top level resources '''
        data = OrderedDict()
        data['ping'] = reverse('api:api_v2_ping_view', request=request)
        data['instances'] = reverse('api:instance_list', request=request)
        data['instance_groups'] = reverse('api:instance_group_list', request=request)
        data['config'] = reverse('api:api_v2_config_view', request=request)
        data['settings'] = reverse('api:setting_category_list', request=request)
        data['me'] = reverse('api:user_me_list', request=request)
        data['dashboard'] = reverse('api:dashboard_view', request=request)
        data['organizations'] = reverse('api:organization_list', request=request)
        data['users'] = reverse('api:user_list', request=request)
        data['projects'] = reverse('api:project_list', request=request)
        data['project_updates'] = reverse('api:project_update_list', request=request)
        data['teams'] = reverse('api:team_list', request=request)
        data['credentials'] = reverse('api:credential_list', request=request)
        data['credential_types'] = reverse('api:credential_type_list', request=request)
        data['credential_input_sources'] = reverse('api:credential_input_source_list', request=request)
        data['applications'] = reverse('api:o_auth2_application_list', request=request)
        data['tokens'] = reverse('api:o_auth2_token_list', request=request)
        data['metrics'] = reverse('api:metrics_view', request=request)
        data['inventory'] = reverse('api:inventory_list', request=request)
        data['inventory_scripts'] = reverse('api:inventory_script_list', request=request)
        data['inventory_sources'] = reverse('api:inventory_source_list', request=request)
        data['inventory_updates'] = reverse('api:inventory_update_list', request=request)
        data['groups'] = reverse('api:group_list', request=request)
        data['hosts'] = reverse('api:host_list', request=request)
        data['job_templates'] = reverse('api:job_template_list', request=request)
        data['jobs'] = reverse('api:job_list', request=request)
        data['job_events'] = reverse('api:job_event_list', request=request)
        data['ad_hoc_commands'] = reverse('api:ad_hoc_command_list', request=request)
        data['system_job_templates'] = reverse('api:system_job_template_list', request=request)
        data['system_jobs'] = reverse('api:system_job_list', request=request)
        data['schedules'] = reverse('api:schedule_list', request=request)
        data['roles'] = reverse('api:role_list', request=request)
        data['notification_templates'] = reverse('api:notification_template_list', request=request)
        data['notifications'] = reverse('api:notification_list', request=request)
        data['labels'] = reverse('api:label_list', request=request)
        data['unified_job_templates'] = reverse('api:unified_job_template_list', request=request)
        data['unified_jobs'] = reverse('api:unified_job_list', request=request)
        data['activity_stream'] = reverse('api:activity_stream_list', request=request)
        data['workflow_job_templates'] = reverse('api:workflow_job_template_list', request=request)
        data['workflow_jobs'] = reverse('api:workflow_job_list', request=request)
        data['workflow_approvals'] = reverse('api:workflow_approval_list', request=request)
        data['workflow_job_template_nodes'] = reverse('api:workflow_job_template_node_list', request=request)
        data['workflow_job_nodes'] = reverse('api:workflow_job_node_list', request=request)
        return Response(data)


class ApiV2RootView(ApiVersionRootView):
    name = _('Version 2')


class ApiV2PingView(APIView):
    """A simple view that reports very basic information about this
    instance, which is acceptable to be public information.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()
    name = _('Ping')
    swagger_topic = 'System Configuration'

    def get(self, request, format=None):
        """Return some basic information about this instance

        Everything returned here should be considered public / insecure, as
        this requires no auth and is intended for use by the installer process.
        """
        response = {
            'ha': is_ha_environment(),
            'version': get_awx_version(),
            'active_node': settings.CLUSTER_HOST_ID,
            'install_uuid': settings.INSTALL_UUID,
        }

        response['instances'] = []
        for instance in Instance.objects.all():
            response['instances'].append(dict(node=instance.hostname, uuid=instance.uuid, heartbeat=instance.modified,
                                              capacity=instance.capacity, version=instance.version))
            sorted(response['instances'], key=operator.itemgetter('node'))
        response['instance_groups'] = []
        for instance_group in InstanceGroup.objects.prefetch_related('instances'):
            response['instance_groups'].append(dict(name=instance_group.name,
                                                    capacity=instance_group.capacity,
                                                    instances=[x.hostname for x in instance_group.instances.all()]))
        return Response(response)


class ApiV2SubscriptionView(APIView):

    permission_classes = (IsAuthenticated,)
    name = _('Configuration')
    swagger_topic = 'System Configuration'

    def check_permissions(self, request):
        super(ApiV2SubscriptionView, self).check_permissions(request)
        if not request.user.is_superuser and request.method.lower() not in {'options', 'head'}:
            self.permission_denied(request)  # Raises PermissionDenied exception.

    def post(self, request):
        from awx.main.utils.common import get_licenser
        data = request.data.copy()
        if data.get('rh_password') == '$encrypted$':
            data['rh_password'] = settings.REDHAT_PASSWORD
        try:
            user, pw = data.get('rh_username'), data.get('rh_password')
            validated = get_licenser().validate_rh(user, pw)
            if user:
                settings.REDHAT_USERNAME = data['rh_username']
            if pw:
                settings.REDHAT_PASSWORD = data['rh_password']
        except Exception as exc:
            msg = _("Invalid License")
            if (
                isinstance(exc, requests.exceptions.HTTPError) and
                getattr(getattr(exc, 'response', None), 'status_code', None) == 401
            ):
                msg = _("The provided credentials are invalid (HTTP 401).")
            if isinstance(exc, (ValueError, OSError)) and exc.args:
                msg = exc.args[0]
            logger.exception(smart_text(u"Invalid license submitted."),
                             extra=dict(actor=request.user.username))
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response(validated)


class ApiV2ConfigView(APIView):

    permission_classes = (IsAuthenticated,)
    name = _('Configuration')
    swagger_topic = 'System Configuration'

    def check_permissions(self, request):
        super(ApiV2ConfigView, self).check_permissions(request)
        if not request.user.is_superuser and request.method.lower() not in {'options', 'head', 'get'}:
            self.permission_denied(request)  # Raises PermissionDenied exception.

    def get(self, request, format=None):
        '''Return various sitewide configuration settings'''

        if request.user.is_superuser or request.user.is_system_auditor:
            license_data = get_license(show_key=True)
        else:
            license_data = get_license(show_key=False)
        if not license_data.get('valid_key', False):
            license_data = {}
        if license_data and 'features' in license_data and 'activity_streams' in license_data['features']:
            # FIXME: Make the final setting value dependent on the feature?
            license_data['features']['activity_streams'] &= settings.ACTIVITY_STREAM_ENABLED

        pendo_state = settings.PENDO_TRACKING_STATE if settings.PENDO_TRACKING_STATE in ('off', 'anonymous', 'detailed') else 'off'

        data = dict(
            time_zone=settings.TIME_ZONE,
            license_info=license_data,
            version=get_awx_version(),
            ansible_version=get_ansible_version(),
            eula=render_to_string("eula.md") if license_data.get('license_type', 'UNLICENSED') != 'open' else '',
            analytics_status=pendo_state,
            become_methods=PRIVILEGE_ESCALATION_METHODS,
        )

        # If LDAP is enabled, user_ldap_fields will return a list of field
        # names that are managed by LDAP and should be read-only for users with
        # a non-empty ldap_dn attribute.
        if getattr(settings, 'AUTH_LDAP_SERVER_URI', None):
            user_ldap_fields = ['username', 'password']
            user_ldap_fields.extend(getattr(settings, 'AUTH_LDAP_USER_ATTR_MAP', {}).keys())
            user_ldap_fields.extend(getattr(settings, 'AUTH_LDAP_USER_FLAGS_BY_GROUP', {}).keys())
            data['user_ldap_fields'] = user_ldap_fields

        if request.user.is_superuser \
                or request.user.is_system_auditor \
                or Organization.accessible_objects(request.user, 'admin_role').exists() \
                or Organization.accessible_objects(request.user, 'auditor_role').exists() \
                or Organization.accessible_objects(request.user, 'project_admin_role').exists():
            data.update(dict(
                project_base_dir = settings.PROJECTS_ROOT,
                project_local_paths = Project.get_local_path_choices(),
                custom_virtualenvs = get_custom_venv_choices()
            ))
        elif JobTemplate.accessible_objects(request.user, 'admin_role').exists():
            data['custom_virtualenvs'] = get_custom_venv_choices()

        return Response(data)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response({"error": _("Invalid license data")}, status=status.HTTP_400_BAD_REQUEST)
        if "eula_accepted" not in request.data:
            return Response({"error": _("Missing 'eula_accepted' property")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            eula_accepted = to_python_boolean(request.data["eula_accepted"])
        except ValueError:
            return Response({"error": _("'eula_accepted' value is invalid")}, status=status.HTTP_400_BAD_REQUEST)

        if not eula_accepted:
            return Response({"error": _("'eula_accepted' must be True")}, status=status.HTTP_400_BAD_REQUEST)
        request.data.pop("eula_accepted")
        try:
            data_actual = json.dumps(request.data)
        except Exception:
            logger.info(smart_text(u"Invalid JSON submitted for license."),
                        extra=dict(actor=request.user.username))
            return Response({"error": _("Invalid JSON")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from awx.main.utils.common import get_licenser
            license_data = json.loads(data_actual)
            license_data_validated = get_licenser(**license_data).validate()
        except Exception:
            logger.warning(smart_text(u"Invalid license submitted."),
                           extra=dict(actor=request.user.username))
            return Response({"error": _("Invalid License")}, status=status.HTTP_400_BAD_REQUEST)

        # If the license is valid, write it to the database.
        if license_data_validated['valid_key']:
            settings.LICENSE = license_data
            settings.TOWER_URL_BASE = "{}://{}".format(request.scheme, request.get_host())
            return Response(license_data_validated)

        logger.warning(smart_text(u"Invalid license submitted."),
                       extra=dict(actor=request.user.username))
        return Response({"error": _("Invalid license")}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            settings.LICENSE = {}
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            # FIX: Log
            return Response({"error": _("Failed to remove license.")}, status=status.HTTP_400_BAD_REQUEST)
