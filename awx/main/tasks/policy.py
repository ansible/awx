import json
import tempfile
import contextlib

from pprint import pformat

from typing import Optional, Union

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from opa_client import OpaClient
from opa_client.base import BaseClient
from requests import HTTPError
from rest_framework import serializers
from rest_framework import fields

from awx.main import models
from awx.main.exceptions import PolicyEvaluationError


# Monkey patching opa_client.base.BaseClient to fix retries and timeout settings
_original_opa_base_client_init = BaseClient.__init__


def _opa_base_client_init_fix(
    self,
    host: str = "localhost",
    port: int = 8181,
    version: str = "v1",
    ssl: bool = False,
    cert: Optional[Union[str, tuple]] = None,
    headers: Optional[dict] = None,
    retries: int = 2,
    timeout: float = 1.5,
):
    _original_opa_base_client_init(self, host, port, version, ssl, cert, headers)
    self.retries = retries
    self.timeout = timeout


BaseClient.__init__ = _opa_base_client_init_fix


class _TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Team
        fields = ('id', 'name')


class _UserSerializer(serializers.ModelSerializer):
    teams = serializers.SerializerMethodField()

    class Meta:
        model = models.User
        fields = ('id', 'username', 'is_superuser', 'teams')

    def get_teams(self, user: models.User):
        teams = models.Team.access_qs(user, 'member')
        return _TeamSerializer(many=True).to_representation(teams)


class _ExecutionEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ExecutionEnvironment
        fields = (
            'id',
            'name',
            'image',
            'pull',
        )


class _InstanceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InstanceGroup
        fields = (
            'id',
            'name',
            'capacity',
            'jobs_running',
            'jobs_total',
            'max_concurrent_jobs',
            'max_forks',
        )


class _InventorySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InventorySource
        fields = ('id', 'name', 'source', 'status')


class _InventorySerializer(serializers.ModelSerializer):
    inventory_sources = _InventorySourceSerializer(many=True)

    class Meta:
        model = models.Inventory
        fields = (
            'id',
            'name',
            'description',
            'kind',
            'total_hosts',
            'total_groups',
            'has_inventory_sources',
            'total_inventory_sources',
            'has_active_failures',
            'hosts_with_active_failures',
            'inventory_sources',
        )


class _JobTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JobTemplate
        fields = (
            'id',
            'name',
            'job_type',
        )


class _WorkflowJobTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowJobTemplate
        fields = (
            'id',
            'name',
            'job_type',
        )


class _WorkflowJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkflowJob
        fields = (
            'id',
            'name',
        )


class _OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organization
        fields = (
            'id',
            'name',
        )


class _ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = (
            'id',
            'name',
            'status',
            'scm_type',
            'scm_url',
            'scm_branch',
            'scm_refspec',
            'scm_clean',
            'scm_track_submodules',
            'scm_delete_on_update',
        )


class _CredentialSerializer(serializers.ModelSerializer):
    organization = _OrganizationSerializer()

    class Meta:
        model = models.Credential
        fields = (
            'id',
            'name',
            'description',
            'organization',
            'credential_type',
            'managed',
            'kind',
            'cloud',
            'kubernetes',
        )


class _LabelSerializer(serializers.ModelSerializer):
    organization = _OrganizationSerializer()

    class Meta:
        model = models.Label
        fields = ('id', 'name', 'organization')


class JobSerializer(serializers.ModelSerializer):
    created_by = _UserSerializer()
    credentials = _CredentialSerializer(many=True)
    execution_environment = _ExecutionEnvironmentSerializer()
    instance_group = _InstanceGroupSerializer()
    inventory = _InventorySerializer()
    job_template = _JobTemplateSerializer()
    labels = _LabelSerializer(many=True)
    organization = _OrganizationSerializer()
    project = _ProjectSerializer()
    extra_vars = fields.SerializerMethodField()
    hosts_count = fields.SerializerMethodField()
    workflow_job = fields.SerializerMethodField()
    workflow_job_template = fields.SerializerMethodField()

    class Meta:
        model = models.Job
        fields = (
            'id',
            'name',
            'created',
            'created_by',
            'credentials',
            'execution_environment',
            'extra_vars',
            'forks',
            'hosts_count',
            'instance_group',
            'inventory',
            'job_template',
            'job_type',
            'job_type_name',
            'labels',
            'launch_type',
            'limit',
            'launched_by',
            'organization',
            'playbook',
            'project',
            'scm_branch',
            'scm_revision',
            'workflow_job',
            'workflow_job_template',
        )

    def get_extra_vars(self, obj: models.Job):
        return json.loads(obj.display_extra_vars())

    def get_hosts_count(self, obj: models.Job):
        return obj.hosts.count()

    def get_workflow_job(self, obj: models.Job):
        workflow_job: models.WorkflowJob = obj.get_workflow_job()
        if workflow_job is None:
            return None
        return _WorkflowJobSerializer().to_representation(workflow_job)

    def get_workflow_job_template(self, obj: models.Job):
        workflow_job: models.WorkflowJob = obj.get_workflow_job()
        if workflow_job is None:
            return None

        workflow_job_template: models.WorkflowJobTemplate = workflow_job.workflow_job_template
        if workflow_job_template is None:
            return None

        return _WorkflowJobTemplateSerializer().to_representation(workflow_job_template)


class OPAResultSerializer(serializers.Serializer):
    allowed = fields.BooleanField(required=True)
    violations = fields.ListField(child=fields.CharField())


class OPA_AUTH_TYPES:
    NONE = 'None'
    TOKEN = 'Token'
    CERTIFICATE = 'Certificate'


@contextlib.contextmanager
def opa_cert_file():
    """
    Context manager that creates temporary certificate files for OPA authentication.

    For mTLS (mutual TLS), we need:
    - Client certificate and key for client authentication
    - CA certificate (optional) for server verification

    Returns:
        tuple: (client_cert_path, verify_path)
            - client_cert_path: Path to client cert file or None if not using client cert
            - verify_path: Path to CA cert file, True to use system CA store, or False for no verification
    """
    client_cert_temp = None
    ca_temp = None

    try:
        # Case 1: Full mTLS with client cert and optional CA cert
        if settings.OPA_AUTH_TYPE == OPA_AUTH_TYPES.CERTIFICATE:
            # Create client certificate file (required for mTLS)
            client_cert_temp = tempfile.NamedTemporaryFile(delete=True, mode='w', suffix=".pem")
            client_cert_temp.write(settings.OPA_AUTH_CLIENT_CERT)
            client_cert_temp.write("\n")
            client_cert_temp.write(settings.OPA_AUTH_CLIENT_KEY)
            client_cert_temp.write("\n")
            client_cert_temp.flush()

            # If CA cert is provided, use it for server verification
            # Otherwise, use system CA store (True)
            if settings.OPA_AUTH_CA_CERT:
                ca_temp = tempfile.NamedTemporaryFile(delete=True, mode='w', suffix=".pem")
                ca_temp.write(settings.OPA_AUTH_CA_CERT)
                ca_temp.write("\n")
                ca_temp.flush()
                verify_path = ca_temp.name
            else:
                verify_path = True  # Use system CA store

            yield (client_cert_temp.name, verify_path)

        # Case 2: TLS with only server verification (no client cert)
        elif settings.OPA_SSL:
            # If CA cert is provided, use it for server verification
            # Otherwise, use system CA store (True)
            if settings.OPA_AUTH_CA_CERT:
                ca_temp = tempfile.NamedTemporaryFile(delete=True, mode='w', suffix=".pem")
                ca_temp.write(settings.OPA_AUTH_CA_CERT)
                ca_temp.write("\n")
                ca_temp.flush()
                verify_path = ca_temp.name
            else:
                verify_path = True  # Use system CA store

            yield (None, verify_path)

        # Case 3: No TLS
        else:
            yield (None, False)

    finally:
        # Clean up temporary files
        if client_cert_temp:
            client_cert_temp.close()
        if ca_temp:
            ca_temp.close()


@contextlib.contextmanager
def opa_client(headers=None):
    with opa_cert_file() as cert_files:
        cert, verify = cert_files

        with OpaClient(
            host=settings.OPA_HOST,
            port=settings.OPA_PORT,
            headers=headers,
            ssl=settings.OPA_SSL,
            cert=cert,
            timeout=settings.OPA_REQUEST_TIMEOUT,
            retries=settings.OPA_REQUEST_RETRIES,
        ) as client:
            # Workaround for https://github.com/Turall/OPA-python-client/issues/32
            # by directly setting cert and verify on requests.session
            client._session.cert = cert
            client._session.verify = verify

            yield client


def evaluate_policy(instance):
    # Policy evaluation for Policy as Code feature
    if not settings.OPA_HOST:
        return

    if not isinstance(instance, models.Job):
        return

    instance.log_lifecycle("evaluate_policy")

    input_data = JobSerializer(instance=instance).data

    headers = settings.OPA_AUTH_CUSTOM_HEADERS
    if settings.OPA_AUTH_TYPE == OPA_AUTH_TYPES.TOKEN:
        headers.update({'Authorization': 'Bearer {}'.format(settings.OPA_AUTH_TOKEN)})

    if settings.OPA_AUTH_TYPE == OPA_AUTH_TYPES.CERTIFICATE and not settings.OPA_SSL:
        raise PolicyEvaluationError(_('OPA_AUTH_TYPE=Certificate requires OPA_SSL to be enabled.'))

    cert_settings_missing = []

    if settings.OPA_AUTH_TYPE == OPA_AUTH_TYPES.CERTIFICATE:
        if not settings.OPA_AUTH_CLIENT_CERT:
            cert_settings_missing += ['OPA_AUTH_CLIENT_CERT']
        if not settings.OPA_AUTH_CLIENT_KEY:
            cert_settings_missing += ['OPA_AUTH_CLIENT_KEY']
        if not settings.OPA_AUTH_CA_CERT:
            cert_settings_missing += ['OPA_AUTH_CA_CERT']

        if cert_settings_missing:
            raise PolicyEvaluationError(_('Following certificate settings are missing for OPA_AUTH_TYPE=Certificate: {}').format(cert_settings_missing))

    query_paths = [
        ('Organization', instance.organization.opa_query_path),
        ('Inventory', instance.inventory.opa_query_path),
        ('Job template', instance.job_template.opa_query_path),
    ]
    violations = dict()
    errors = dict()

    try:
        with opa_client(headers=headers) as client:
            for path_type, query_path in query_paths:
                response = dict()
                try:
                    if not query_path:
                        continue

                    response = client.query_rule(input_data=input_data, package_path=query_path)

                except HTTPError as e:
                    message = _('Call to OPA failed. Exception: {}').format(e)
                    try:
                        error_data = e.response.json()
                    except ValueError:
                        errors[path_type] = message
                        continue

                    error_code = error_data.get("code")
                    error_message = error_data.get("message")
                    if error_code or error_message:
                        message = _('Call to OPA failed. Code: {}, Message: {}').format(error_code, error_message)
                    errors[path_type] = message
                    continue

                except Exception as e:
                    errors[path_type] = _('Call to OPA failed. Exception: {}').format(e)
                    continue

                result = response.get('result')
                if result is None:
                    errors[path_type] = _('Call to OPA did not return a "result" property. The path refers to an undefined document.')
                    continue

                result_serializer = OPAResultSerializer(data=result)
                if not result_serializer.is_valid():
                    errors[path_type] = _('OPA policy returned invalid result.')
                    continue

                result_data = result_serializer.validated_data
                if not result_data.get("allowed") and (result_violations := result_data.get("violations")):
                    violations[path_type] = result_violations

            format_results = dict()
            if any(errors[e] for e in errors):
                format_results["Errors"] = errors

            if any(violations[v] for v in violations):
                format_results["Violations"] = violations

            if violations or errors:
                raise PolicyEvaluationError(pformat(format_results, width=80))

    except Exception as e:
        raise PolicyEvaluationError(_('This job cannot be executed due to a policy violation or error. See the following details:\n{}').format(e))
