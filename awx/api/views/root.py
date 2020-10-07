# Copyright (c) 2018 Ansible, Inc.
# All Rights Reserved.

import os
import json
import logging
import operator
from collections import OrderedDict
import random

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
from awx.conf.registry import settings_registry
from awx.main.analytics import all_collectors
from awx.main.ha import is_ha_environment
from awx.main.utils import (
    get_awx_version,
    get_ansible_version,
    get_custom_venv_choices,
    to_python_boolean,
)
from awx.api.versioning import reverse, drf_reverse
from awx.main.constants import PRIVILEGE_ESCALATION_METHODS
from awx.main.models import (
    Project,
    Organization,
    Instance,
    InstanceGroup,
    JobTemplate,
)
from awx.main.utils import set_environ

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
        data['login_redirect_override'] = settings.LOGIN_REDIRECT_OVERRIDE
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
    name = _('Subscriptions')
    swagger_topic = 'System Configuration'

    def check_permissions(self, request):
        super(ApiV2SubscriptionView, self).check_permissions(request)
        if not request.user.is_superuser and request.method.lower() not in {'options', 'head'}:
            self.permission_denied(request)  # Raises PermissionDenied exception.

    def post(self, request):
        from awx.main.utils.common import get_licenser
        data = request.data.copy()
        if data.get('subscriptions_password') == '$encrypted$':
            data['subscriptions_password'] = settings.SUBSCRIPTIONS_PASSWORD
        try:
            user, pw = data.get('subscriptions_username'), data.get('subscriptions_password')
            with set_environ(**settings.AWX_TASK_ENV):
                validated = get_licenser().validate_rh(user, pw)
            if user:
                settings.SUBSCRIPTIONS_USERNAME = data['subscriptions_username']
            if pw:
                settings.SUBSCRIPTIONS_PASSWORD = data['subscriptions_password']
        except Exception as exc:
            msg = _("Invalid License")
            if (
                isinstance(exc, requests.exceptions.HTTPError) and
                getattr(getattr(exc, 'response', None), 'status_code', None) == 401
            ):
                msg = _("The provided credentials are invalid (HTTP 401).")
            elif isinstance(exc, requests.exceptions.ProxyError):
                msg = _("Unable to connect to proxy server.")
            elif isinstance(exc, requests.exceptions.ConnectionError):
                msg = _("Could not connect to subscription service.")
            elif isinstance(exc, (ValueError, OSError)) and exc.args:
                msg = exc.args[0]
            else:
                logger.exception(smart_text(u"Invalid license submitted."),
                                 extra=dict(actor=request.user.username))
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

        return Response(validated)


class ApiV2AttachView(APIView):

    permission_classes = (IsAuthenticated,)
    name = _('Attach Subscription')
    swagger_topic = 'System Configuration'

    def check_permissions(self, request):
        super(ApiV2AttachView, self).check_permissions(request)
        if not request.user.is_superuser and request.method.lower() not in {'options', 'head'}:
            self.permission_denied(request)  # Raises PermissionDenied exception.

    def post(self, request):
        data = request.data.copy()
        pool_id = data.get('pool_id', None)
        org = data.get('org', None)
        if not pool_id:
            return Response({"error": _("No subscription pool ID provided.")}, status=status.HTTP_400_BAD_REQUEST)
        user = getattr(settings, 'SUBSCRIPTIONS_USERNAME', None)
        pw = getattr(settings, 'SUBSCRIPTIONS_PASSWORD', None)
        if pool_id and user and pw:
            try:
                # Create connection
                from rhsm.connection import UEPConnection, RestlibException, UnauthorizedException
                uep = UEPConnection(username=user, password=pw, insecure=True)

                # Check if consumer already exists
                consumer = getattr(settings, 'ENTITLEMENT_CONSUMER', dict())

                # Get owner/org list
                orgs = uep.getOwnerList(user)
                org_ids = []
                for item in orgs:
                    org_ids.append(item['key'])
                if org:
                    if org not in org_ids:
                        return Response({"error": _("No organizations with that ID are associated with that account")}, status=status.HTTP_400_BAD_REQUEST)

                else:
                    if len(orgs) == 0:
                        return Response({"error": _("No organizations associated with that account")}, status=status.HTTP_400_BAD_REQUEST)
                    # Request org if there are multiple as we cannot be sure which the user intends to use
                    if len(orgs) > 1:
                        return Response({"error": _("You must specify your Satellite Organization")}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        # Try the first owner key when creating consumer
                        org = orgs[0]['key']

                # Use org key if provided, but not already on consumer record in db
                if not getattr(consumer, 'org', None) and consumer != {}:
                    consumer['org'] = org
                if consumer == {}:
                    consumer['org'] = org
                    consumer['name'] = "Ansible-Tower-" + str(random.randint(1,1000000000))
                    # Gather facts
                    install_type = 'traditional'
                    if os.environ.get('container') == 'oci':
                        install_type = 'openshift'
                    elif 'KUBERNETES_SERVICE_PORT' in os.environ:
                        install_type = 'k8s'
                    facts = {
                        "system.certificate_version": "3.2",
                        "tower.cluster_uuid": str(settings.INSTALL_UUID),
                        "tower.install_type": install_type,
                        "uname.machine": "x86_64",
                    }
                    try:
                        # Register consumer
                        consumer_resp = uep.registerConsumer(name=consumer['name'], type="system", owner=consumer['org'], facts=facts)
                        consumer['uuid'] = consumer_resp['uuid']
                    except RestlibException as e:
                        if e.code == 404 and 'owner with key' in e.msg:
                            return Response({"error": _("Satellite Organization does not exist. ")}, status=status.HTTP_400_BAD_REQUEST)
                        return Response({"error": _("You must specify your Satellite Organization")}, status=status.HTTP_400_BAD_REQUEST)
                    except Exception as e:
                        logger.exception(e)
                        pass

                # Save consumer_uuid in db
                settings.ENTITLEMENT_CONSUMER = consumer

                # Attach subscription to consumer
                try:
                    attach = uep.bindByEntitlementPool(consumerId=consumer['uuid'], poolId=pool_id, quantity=None)
                    consumer['serial_id'] = str(attach[0]['certificates'][0]['serial']['id'])
                except Exception as e:
                    # A 404 was received because pool does not exist for this consumer
                    # A 403 was recieved because the sub was already attached to this consumer
                    # Or the subscription could not be attached to this consumer
                    return Response({"error": _("Unable to attach selected subscription to consumer. " + str(e))}, status=status.HTTP_400_BAD_REQUEST)

                # Save consumer_uuid in db
                settings.ENTITLEMENT_CONSUMER = consumer

                # Attempt to get entitlement cert from RHSM 
                entitlements = uep.getCertificates(consumer_uuid=consumer['uuid'], serials=[consumer['serial_id']])
                # Concatenate certs and keys for the associated entitlement together
                cert_key = ''

                for entitlement in entitlements:
                    cert_key = entitlement['cert'] + entitlement['key']  # Potentially make this `=` --> '+=' to accomodate multiple certs/keys?

                # Save the cert as a setting
                if cert_key != '':
                    settings.ENTITLEMENT_CERT = cert_key
                else:
                    return Response({"error": _("Could not attach subscription or find entitlement certificate.")}, status=status.HTTP_400_BAD_REQUEST)

                # Return a 200 to denote the subscription has been successfully attached
                # The UI will now make a separate POST to the config endpoint to validate and apply entitlement cert
                return Response({}, status=status.HTTP_200_OK)


            except Exception as e:

                msg = _("Invalid Subscription.")
                # TODO: Catch specific errors
                if (
                    isinstance(e, UnauthorizedException) and
                    getattr(e, 'code', None) == 401
                ):
                    msg = _("The provided credentials are invalid (HTTP 401). Content host: " + uep.host + \
                        "; Register this node with the correct content host via subscription-manager.")

                # elif isinstance(exc, requests.exceptions.ProxyError):
                #     msg = _("Unable to connect to proxy server.")
                # elif isinstance(exc, requests.exceptions.ConnectionError):
                #     msg = _("Could not connect to subscription service.")
                # elif isinstance(exc, (ValueError, OSError)) and exc.args:
                #     msg = exc.args[0]
                # else:
                #     logger.exception(smart_text(u"Invalid license submitted."),
                #                      extra=dict(actor=request.user.username))
                return Response({"error": msg + e}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"error": _("No pool_id provided, or SUBSCRIPTIONS_USERNAME and SUBSCRIPTIONS_PASSWORD are not set.")}, 
                        status=status.HTTP_400_BAD_REQUEST)


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

        from awx.main.utils.common import get_licenser
        license_data = get_licenser().validate(new_cert=False)

        if not license_data.get('valid_key', False):
            license_data = {}

        pendo_state = settings.PENDO_TRACKING_STATE if settings.PENDO_TRACKING_STATE in ('off', 'anonymous', 'detailed') else 'off'

        data = dict(
            time_zone=settings.TIME_ZONE,
            license_info=license_data,
            version=get_awx_version(),
            ansible_version=get_ansible_version(),
            eula=render_to_string("eula.md") if license_data.get('license_type', 'UNLICENSED') != 'open' else '',
            analytics_status=pendo_state,
            analytics_collectors=all_collectors(),
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

        # Save Entitlement Cert/Key
        license_data = json.loads(data_actual)
        if 'entitlement_cert' in license_data:
            settings.ENTITLEMENT_CERT = license_data['entitlement_cert']

        try:
            # Validate entitlement cert and get subscription metadata
            # validate() will clear the entitlement cert if not valid
            from awx.main.utils.common import get_licenser
            license_data_validated = get_licenser().validate(new_cert=True)
        except Exception:
            logger.warning(smart_text(u"Invalid license submitted."),
                           extra=dict(actor=request.user.username))
            # If License invalid, clear entitlment cert value
            settings.ENTITLEMENT_CERT = ''
            return Response({"error": _("Invalid License")}, status=status.HTTP_400_BAD_REQUEST)

        # If the license is valid, write it to the database.
        if license_data_validated['valid_key']:
            if not settings_registry.is_setting_read_only('TOWER_URL_BASE'):
                settings.TOWER_URL_BASE = "{}://{}".format(request.scheme, request.get_host())
            return Response(license_data_validated)

        logger.warning(smart_text(u"Invalid license submitted."),
                       extra=dict(actor=request.user.username))
        return Response({"error": _("Invalid license")}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        try:
            settings.LICENSE = {}
            settings.ENTITLEMENT_CERT = ''
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            # FIX: Log
            return Response({"error": _("Failed to remove license.")}, status=status.HTTP_400_BAD_REQUEST)
        
