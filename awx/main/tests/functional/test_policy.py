import json
import os
from unittest import mock

import pytest
import requests.exceptions
from django.test import override_settings

from awx.main.models import (
    Job,
    Inventory,
    Project,
    Organization,
    JobTemplate,
    Credential,
    CredentialType,
    User,
    Team,
    Label,
    WorkflowJob,
    WorkflowJobNode,
    InventorySource,
)
from awx.main.exceptions import PolicyEvaluationError
from awx.main.tasks import policy
from awx.main.tasks.policy import JobSerializer, OPA_AUTH_TYPES


def _parse_exception_message(exception: PolicyEvaluationError):
    pe_plain = str(exception.value)

    assert "This job cannot be executed due to a policy violation or error. See the following details:" in pe_plain

    violation_message = "This job cannot be executed due to a policy violation or error. See the following details:"
    return eval(pe_plain.split(violation_message)[1].strip())


@pytest.fixture(autouse=True)
def setup_opa_settings():
    with override_settings(
        OPA_HOST='opa.example.com',
    ):
        yield


@pytest.fixture
def opa_client():
    cls_mock = mock.MagicMock(name='OpaClient')
    instance_mock = cls_mock.return_value
    instance_mock.__enter__.return_value = instance_mock

    with mock.patch('awx.main.tasks.policy.OpaClient', cls_mock):
        yield instance_mock


@pytest.fixture
def job():
    project: Project = Project.objects.create(name='proj1', scm_type='git', scm_branch='main', scm_url='https://git.example.com/proj1')
    inventory: Inventory = Inventory.objects.create(name='inv1', opa_query_path="inventory/response")
    org: Organization = Organization.objects.create(name="org1", opa_query_path="organization/response")
    jt: JobTemplate = JobTemplate.objects.create(name="jt1", opa_query_path="job_template/response")
    job: Job = Job.objects.create(name='job1', extra_vars="{}", inventory=inventory, project=project, organization=org, job_template=jt)
    return job


@pytest.mark.django_db
def test_job_serializer():
    user: User = User.objects.create(username='user1')
    org: Organization = Organization.objects.create(name='org1')

    team: Team = Team.objects.create(name='team1', organization=org)
    team.admin_role.members.add(user)

    project: Project = Project.objects.create(name='proj1', scm_type='git', scm_branch='main', scm_url='https://git.example.com/proj1')
    inventory: Inventory = Inventory.objects.create(name='inv1', description='Demo inventory')
    inventory_source: InventorySource = InventorySource.objects.create(name='inv-src1', source='file', inventory=inventory)
    extra_vars = {"FOO": "value1", "BAR": "value2"}

    CredentialType.setup_tower_managed_defaults()
    cred_type_ssh: CredentialType = CredentialType.objects.get(kind='ssh')
    cred: Credential = Credential.objects.create(name="cred1", description='Demo credential', credential_type=cred_type_ssh, organization=org)

    label: Label = Label.objects.create(name='label1', organization=org)

    job: Job = Job.objects.create(
        name='job1', extra_vars=json.dumps(extra_vars), inventory=inventory, project=project, organization=org, created_by=user, launch_type='workflow'
    )
    # job.unified_job_node.workflow_job = workflow_job
    job.credentials.add(cred)
    job.labels.add(label)

    workflow_job: WorkflowJob = WorkflowJob.objects.create(name='wf-job1')
    WorkflowJobNode.objects.create(job=job, workflow_job=workflow_job)

    serializer = JobSerializer(instance=job)

    assert serializer.data == {
        'id': job.id,
        'name': 'job1',
        'created': job.created.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        'created_by': {
            'id': user.id,
            'username': 'user1',
            'is_superuser': False,
            'teams': [
                {'id': team.id, 'name': 'team1'},
            ],
        },
        'credentials': [
            {
                'id': cred.id,
                'name': 'cred1',
                'description': 'Demo credential',
                'organization': {
                    'id': org.id,
                    'name': 'org1',
                },
                'credential_type': cred_type_ssh.id,
                'kind': 'ssh',
                'managed': False,
                'kubernetes': False,
                'cloud': False,
            },
        ],
        'execution_environment': None,
        'extra_vars': extra_vars,
        'forks': 0,
        'hosts_count': 0,
        'instance_group': None,
        'inventory': {
            'id': inventory.id,
            'name': 'inv1',
            'description': 'Demo inventory',
            'kind': '',
            'total_hosts': 0,
            'total_groups': 0,
            'has_inventory_sources': False,
            'total_inventory_sources': 0,
            'has_active_failures': False,
            'hosts_with_active_failures': 0,
            'inventory_sources': [
                {
                    'id': inventory_source.id,
                    'name': 'inv-src1',
                    'source': 'file',
                    'status': 'never updated',
                }
            ],
        },
        'job_template': None,
        'job_type': 'run',
        'job_type_name': 'job',
        'labels': [
            {
                'id': label.id,
                'name': 'label1',
                'organization': {
                    'id': org.id,
                    'name': 'org1',
                },
            },
        ],
        'launch_type': 'workflow',
        'limit': '',
        'launched_by': {},
        'organization': {
            'id': org.id,
            'name': 'org1',
        },
        'playbook': '',
        'project': {
            'id': project.id,
            'name': 'proj1',
            'status': 'pending',
            'scm_type': 'git',
            'scm_url': 'https://git.example.com/proj1',
            'scm_branch': 'main',
            'scm_refspec': '',
            'scm_clean': False,
            'scm_track_submodules': False,
            'scm_delete_on_update': False,
        },
        'scm_branch': '',
        'scm_revision': '',
        'workflow_job': {
            'id': workflow_job.id,
            'name': 'wf-job1',
        },
        'workflow_job_template': None,
    }


@pytest.mark.django_db
def test_evaluate_policy_missing_opa_query_path_field(opa_client):
    project: Project = Project.objects.create(name='proj1', scm_type='git', scm_branch='main', scm_url='https://git.example.com/proj1')
    inventory: Inventory = Inventory.objects.create(name='inv1')
    org: Organization = Organization.objects.create(name="org1")
    jt: JobTemplate = JobTemplate.objects.create(name="jt1")
    job: Job = Job.objects.create(name='job1', extra_vars="{}", inventory=inventory, project=project, organization=org, job_template=jt)

    response = {
        "result": {
            "allowed": True,
            "violations": [],
        }
    }
    opa_client.query_rule.return_value = response
    try:
        policy.evaluate_policy(job)
    except PolicyEvaluationError as e:
        pytest.fail(f"Must not raise PolicyEvaluationError: {e}")

    assert opa_client.query_rule.call_count == 0


@pytest.mark.django_db
def test_evaluate_policy(opa_client, job):
    response = {
        "result": {
            "allowed": True,
            "violations": [],
        }
    }
    opa_client.query_rule.return_value = response
    try:
        policy.evaluate_policy(job)
    except PolicyEvaluationError as e:
        pytest.fail(f"Must not raise PolicyEvaluationError: {e}")

    opa_client.query_rule.assert_has_calls(
        [
            mock.call(input_data=mock.ANY, package_path='organization/response'),
            mock.call(input_data=mock.ANY, package_path='inventory/response'),
            mock.call(input_data=mock.ANY, package_path='job_template/response'),
        ],
        any_order=False,
    )
    assert opa_client.query_rule.call_count == 3


@pytest.mark.django_db
def test_evaluate_policy_allowed(opa_client, job):
    response = {
        "result": {
            "allowed": True,
            "violations": [],
        }
    }
    opa_client.query_rule.return_value = response
    try:
        policy.evaluate_policy(job)
    except PolicyEvaluationError as e:
        pytest.fail(f"Must not raise PolicyEvaluationError: {e}")

    assert opa_client.query_rule.call_count == 3


@pytest.mark.django_db
def test_evaluate_policy_not_allowed(opa_client, job):
    response = {
        "result": {
            "allowed": False,
            "violations": ["Access not allowed."],
        }
    }
    opa_client.query_rule.return_value = response

    with pytest.raises(PolicyEvaluationError) as pe:
        policy.evaluate_policy(job)

    pe_plain = str(pe.value)
    assert "Errors:" not in pe_plain

    exception = _parse_exception_message(pe)

    assert exception["Violations"]["Organization"] == ["Access not allowed."]
    assert exception["Violations"]["Inventory"] == ["Access not allowed."]
    assert exception["Violations"]["Job template"] == ["Access not allowed."]

    assert opa_client.query_rule.call_count == 3


@pytest.mark.django_db
def test_evaluate_policy_not_found(opa_client, job):
    response = {}
    opa_client.query_rule.return_value = response

    with pytest.raises(PolicyEvaluationError) as pe:
        policy.evaluate_policy(job)

    missing_result_property = 'Call to OPA did not return a "result" property. The path refers to an undefined document.'

    exception = _parse_exception_message(pe)
    assert exception["Errors"]["Organization"] == missing_result_property
    assert exception["Errors"]["Inventory"] == missing_result_property
    assert exception["Errors"]["Job template"] == missing_result_property

    assert opa_client.query_rule.call_count == 3


@pytest.mark.django_db
def test_evaluate_policy_server_error(opa_client, job):
    http_error_msg = '500 Server Error: Internal Server Error for url: https://opa.example.com:8181/v1/data/job_template/response/invalid'
    error_response = {
        'code': 'internal_error',
        'message': (
            '1 error occurred: 1:1: rego_type_error: undefined ref: data.job_template.response.invalid\n\t'
            'data.job_template.response.invalid\n\t'
            '                           ^\n\t'
            '                           have: "invalid"\n\t'
            '                           want (one of): ["allowed" "violations"]'
        ),
    }
    response = mock.Mock()
    response.status_code = requests.codes.internal_server_error
    response.json.return_value = error_response

    opa_client.query_rule.side_effect = requests.exceptions.HTTPError(http_error_msg, response=response)

    with pytest.raises(PolicyEvaluationError) as pe:
        policy.evaluate_policy(job)

    exception = _parse_exception_message(pe)
    assert exception["Errors"]["Organization"] == f'Call to OPA failed. Code: internal_error, Message: {error_response["message"]}'
    assert exception["Errors"]["Inventory"] == f'Call to OPA failed. Code: internal_error, Message: {error_response["message"]}'
    assert exception["Errors"]["Job template"] == f'Call to OPA failed. Code: internal_error, Message: {error_response["message"]}'

    assert opa_client.query_rule.call_count == 3


@pytest.mark.django_db
def test_evaluate_policy_invalid_result(opa_client, job):
    response = {
        "result": {
            "absolutely": "no!",
        }
    }
    opa_client.query_rule.return_value = response

    with pytest.raises(PolicyEvaluationError) as pe:
        policy.evaluate_policy(job)

    invalid_result = 'OPA policy returned invalid result.'

    exception = _parse_exception_message(pe)
    assert exception["Errors"]["Organization"] == invalid_result
    assert exception["Errors"]["Inventory"] == invalid_result
    assert exception["Errors"]["Job template"] == invalid_result

    assert opa_client.query_rule.call_count == 3


@pytest.mark.django_db
def test_evaluate_policy_failed_exception(opa_client, job):
    error_response = {}
    response = mock.Mock()
    response.status_code = requests.codes.internal_server_error
    response.json.return_value = error_response

    opa_client.query_rule.side_effect = ValueError("Invalid JSON")

    with pytest.raises(PolicyEvaluationError) as pe:
        policy.evaluate_policy(job)

    opa_failed_exception = 'Call to OPA failed. Exception: Invalid JSON'

    exception = _parse_exception_message(pe)
    assert exception["Errors"]["Organization"] == opa_failed_exception
    assert exception["Errors"]["Inventory"] == opa_failed_exception
    assert exception["Errors"]["Job template"] == opa_failed_exception

    assert opa_client.query_rule.call_count == 3


@pytest.mark.django_db
@pytest.mark.parametrize(
    "settings_kwargs, expected_client_cert, expected_verify, verify_content",
    [
        # Case 1: Certificate-based authentication (mTLS)
        (
            {
                "OPA_HOST": "opa.example.com",
                "OPA_SSL": True,
                "OPA_AUTH_TYPE": OPA_AUTH_TYPES.CERTIFICATE,
                "OPA_AUTH_CLIENT_CERT": "-----BEGIN CERTIFICATE-----\nMIICert\n-----END CERTIFICATE-----",
                "OPA_AUTH_CLIENT_KEY": "-----BEGIN PRIVATE KEY-----\nMIIKey\n-----END PRIVATE KEY-----",
                "OPA_AUTH_CA_CERT": "-----BEGIN CERTIFICATE-----\nMIICACert\n-----END CERTIFICATE-----",
            },
            True,  # Client cert should be created
            "file",  # Verify path should be a file
            "-----BEGIN CERTIFICATE-----",  # Expected content in verify file
        ),
        # Case 2: SSL with server verification only
        (
            {
                "OPA_HOST": "opa.example.com",
                "OPA_SSL": True,
                "OPA_AUTH_TYPE": OPA_AUTH_TYPES.NONE,
                "OPA_AUTH_CA_CERT": "-----BEGIN CERTIFICATE-----\nMIICACert\n-----END CERTIFICATE-----",
            },
            False,  # No client cert should be created
            "file",  # Verify path should be a file
            "-----BEGIN CERTIFICATE-----",  # Expected content in verify file
        ),
        # Case 3: SSL with system CA store
        (
            {
                "OPA_HOST": "opa.example.com",
                "OPA_SSL": True,
                "OPA_AUTH_TYPE": OPA_AUTH_TYPES.NONE,
                "OPA_AUTH_CA_CERT": "",  # No custom CA cert
            },
            False,  # No client cert should be created
            True,  # Verify path should be True (system CA store)
            None,  # No file to check content
        ),
        # Case 4: No SSL
        (
            {
                "OPA_HOST": "opa.example.com",
                "OPA_SSL": False,
                "OPA_AUTH_TYPE": OPA_AUTH_TYPES.NONE,
            },
            False,  # No client cert should be created
            False,  # Verify path should be False (no verification)
            None,  # No file to check content
        ),
    ],
    ids=[
        "certificate_auth",
        "ssl_server_verification",
        "ssl_system_ca_store",
        "no_ssl",
    ],
)
def test_opa_cert_file(settings_kwargs, expected_client_cert, expected_verify, verify_content):
    """Parameterized test for the opa_cert_file context manager.

    Tests different configurations:
    - Certificate-based authentication (mTLS)
    - SSL with server verification only
    - SSL with system CA store
    - No SSL
    """
    with override_settings(**settings_kwargs):
        client_cert_path = None
        verify_path = None

        with policy.opa_cert_file() as cert_files:
            client_cert_path, verify_path = cert_files

            # Check client cert based on expected_client_cert
            if expected_client_cert:
                assert client_cert_path is not None
                with open(client_cert_path, 'r') as f:
                    content = f.read()
                    assert "-----BEGIN CERTIFICATE-----" in content
                    assert "-----BEGIN PRIVATE KEY-----" in content
            else:
                assert client_cert_path is None

            # Check verify path based on expected_verify
            if expected_verify == "file":
                assert verify_path is not None
                assert os.path.isfile(verify_path)
                with open(verify_path, 'r') as f:
                    content = f.read()
                    assert verify_content in content
            else:
                assert verify_path is expected_verify

        # Verify files are deleted after context manager exits
        if expected_client_cert:
            assert not os.path.exists(client_cert_path), "Client cert file was not deleted"

        if expected_verify == "file":
            assert not os.path.exists(verify_path), "CA cert file was not deleted"


@pytest.mark.django_db
@override_settings(
    OPA_HOST='opa.example.com',
    OPA_SSL=False,  # SSL disabled
    OPA_AUTH_TYPE=OPA_AUTH_TYPES.CERTIFICATE,  # But cert auth enabled
    OPA_AUTH_CLIENT_CERT="-----BEGIN CERTIFICATE-----\nMIICert\n-----END CERTIFICATE-----",
    OPA_AUTH_CLIENT_KEY="-----BEGIN PRIVATE KEY-----\nMIIKey\n-----END PRIVATE KEY-----",
)
def test_evaluate_policy_cert_auth_requires_ssl():
    """Test that policy evaluation raises an error when certificate auth is used without SSL."""
    project = Project.objects.create(name='proj1')
    inventory = Inventory.objects.create(name='inv1', opa_query_path="inventory/response")
    org = Organization.objects.create(name="org1", opa_query_path="organization/response")
    jt = JobTemplate.objects.create(name="jt1", opa_query_path="job_template/response")
    job = Job.objects.create(name='job1', extra_vars="{}", inventory=inventory, project=project, organization=org, job_template=jt)

    with pytest.raises(PolicyEvaluationError) as pe:
        policy.evaluate_policy(job)

    assert "OPA_AUTH_TYPE=Certificate requires OPA_SSL to be enabled" in str(pe.value)


@pytest.mark.django_db
@override_settings(
    OPA_HOST='opa.example.com',
    OPA_SSL=True,
    OPA_AUTH_TYPE=OPA_AUTH_TYPES.CERTIFICATE,
    OPA_AUTH_CLIENT_CERT="",  # Missing client cert
    OPA_AUTH_CLIENT_KEY="",  # Missing client key
    OPA_AUTH_CA_CERT="",  # Missing CA cert
)
def test_evaluate_policy_missing_cert_settings():
    """Test that policy evaluation raises an error when certificate settings are missing."""
    project = Project.objects.create(name='proj1')
    inventory = Inventory.objects.create(name='inv1', opa_query_path="inventory/response")
    org = Organization.objects.create(name="org1", opa_query_path="organization/response")
    jt = JobTemplate.objects.create(name="jt1", opa_query_path="job_template/response")
    job = Job.objects.create(name='job1', extra_vars="{}", inventory=inventory, project=project, organization=org, job_template=jt)

    with pytest.raises(PolicyEvaluationError) as pe:
        policy.evaluate_policy(job)

    error_msg = str(pe.value)
    assert "Following certificate settings are missing for OPA_AUTH_TYPE=Certificate:" in error_msg
    assert "OPA_AUTH_CLIENT_CERT" in error_msg
    assert "OPA_AUTH_CLIENT_KEY" in error_msg
    assert "OPA_AUTH_CA_CERT" in error_msg


@pytest.mark.django_db
@override_settings(
    OPA_HOST='opa.example.com',
    OPA_PORT=8181,
    OPA_SSL=True,
    OPA_AUTH_TYPE=OPA_AUTH_TYPES.CERTIFICATE,
    OPA_AUTH_CLIENT_CERT="-----BEGIN CERTIFICATE-----\nMIICert\n-----END CERTIFICATE-----",
    OPA_AUTH_CLIENT_KEY="-----BEGIN PRIVATE KEY-----\nMIIKey\n-----END PRIVATE KEY-----",
    OPA_AUTH_CA_CERT="-----BEGIN CERTIFICATE-----\nMIICACert\n-----END CERTIFICATE-----",
    OPA_REQUEST_TIMEOUT=2.5,
    OPA_REQUEST_RETRIES=3,
)
def test_opa_client_context_manager_mtls():
    """Test that opa_client context manager correctly initializes the OPA client."""
    # Mock the OpaClient class
    with mock.patch('awx.main.tasks.policy.OpaClient') as mock_opa_client:
        # Setup the mock
        mock_instance = mock_opa_client.return_value
        mock_instance.__enter__.return_value = mock_instance
        mock_instance._session = mock.MagicMock()

        # Use the context manager
        with policy.opa_client(headers={'Custom-Header': 'Value'}) as client:
            # Verify the client was initialized with the correct parameters
            mock_opa_client.assert_called_once_with(
                host='opa.example.com',
                port=8181,
                headers={'Custom-Header': 'Value'},
                ssl=True,
                cert=mock.ANY,  # We can't check the exact value as it's a temporary file
                timeout=2.5,
                retries=3,
            )

            # Verify the session properties were set correctly
            assert client._session.cert is not None
            assert client._session.verify is not None

            # Check the content of the cert file
            cert_file_path = client._session.cert
            assert os.path.isfile(cert_file_path)
            with open(cert_file_path, 'r') as f:
                cert_content = f.read()
                assert "-----BEGIN CERTIFICATE-----" in cert_content
                assert "MIICert" in cert_content
                assert "-----BEGIN PRIVATE KEY-----" in cert_content
                assert "MIIKey" in cert_content

            # Check the content of the verify file
            verify_file_path = client._session.verify
            assert os.path.isfile(verify_file_path)
            with open(verify_file_path, 'r') as f:
                verify_content = f.read()
                assert "-----BEGIN CERTIFICATE-----" in verify_content
                assert "MIICACert" in verify_content

            # Verify the client is the mocked instance
            assert client is mock_instance

            # Store file paths for checking after context exit
            cert_path = client._session.cert
            verify_path = client._session.verify

        # Verify files are deleted after context manager exits
        assert not os.path.exists(cert_path), "Client cert file was not deleted"
        assert not os.path.exists(verify_path), "CA cert file was not deleted"


@pytest.mark.django_db
@override_settings(
    OPA_HOST='opa.example.com',
    OPA_SSL=True,
    OPA_AUTH_TYPE=OPA_AUTH_TYPES.TOKEN,
    OPA_AUTH_TOKEN='secret-token',
    OPA_AUTH_CUSTOM_HEADERS={'X-Custom': 'Header'},
)
def test_opa_client_token_auth():
    """Test that token authentication correctly adds the Authorization header."""
    # Create a job for testing
    project = Project.objects.create(name='proj1')
    inventory = Inventory.objects.create(name='inv1', opa_query_path="inventory/response")
    org = Organization.objects.create(name="org1", opa_query_path="organization/response")
    jt = JobTemplate.objects.create(name="jt1", opa_query_path="job_template/response")
    job = Job.objects.create(name='job1', extra_vars="{}", inventory=inventory, project=project, organization=org, job_template=jt)

    # Mock the OpaClient class
    with mock.patch('awx.main.tasks.policy.opa_client') as mock_opa_client_cm:
        # Setup the mock
        mock_client = mock.MagicMock()
        mock_opa_client_cm.return_value.__enter__.return_value = mock_client
        mock_client.query_rule.return_value = {
            "result": {
                "allowed": True,
                "violations": [],
            }
        }

        # Call evaluate_policy
        policy.evaluate_policy(job)

        # Verify opa_client was called with the correct headers
        expected_headers = {'X-Custom': 'Header', 'Authorization': 'Bearer secret-token'}
        mock_opa_client_cm.assert_called_once_with(headers=expected_headers)
