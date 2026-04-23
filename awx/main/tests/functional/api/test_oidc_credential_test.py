"""
Tests for OIDC workload identity credential test endpoints.

Tests the /api/v2/credentials/<id>/test/ and /api/v2/credential_types/<id>/test/
endpoints when used with OIDC-enabled credential types.
"""

import pytest
from unittest import mock

from django.test import override_settings

from awx.main.models import Credential, CredentialType, JobTemplate
from awx.api.versioning import reverse


@pytest.fixture
def job_template(organization, project):
    """Job template with organization and project for OIDC JWT generation."""
    return JobTemplate.objects.create(name='test-jt', organization=organization, project=project, playbook='helloworld.yml')


@pytest.fixture
def oidc_credentialtype():
    """Create a credential type with workload_identity_token internal field."""
    oidc_type_inputs = {
        'fields': [
            {'id': 'url', 'label': 'Vault URL', 'type': 'string', 'help_text': 'The Vault server URL.'},
            {'id': 'auth_path', 'label': 'Auth Path', 'type': 'string', 'help_text': 'JWT auth mount path.'},
            {'id': 'role_id', 'label': 'Role ID', 'type': 'string', 'help_text': 'Vault role.'},
            {'id': 'jwt_aud', 'label': 'JWT Audience', 'type': 'string', 'help_text': 'Expected audience.'},
            {'id': 'workload_identity_token', 'label': 'Workload Identity Token', 'type': 'string', 'secret': True, 'internal': True},
        ],
        'metadata': [
            {'id': 'secret_path', 'label': 'Secret Path', 'type': 'string'},
            {'id': 'job_template_id', 'label': 'Job Template ID', 'type': 'string'},
        ],
        'required': ['url', 'auth_path', 'role_id'],
    }

    class MockPlugin(object):
        def backend(self, **kwargs):
            # Simulate successful backend call
            return 'secret'

    with mock.patch('awx.main.models.credential.CredentialType.plugin', new_callable=mock.PropertyMock) as mock_plugin:
        mock_plugin.return_value = MockPlugin()
        oidc_type = CredentialType(kind='external', managed=True, namespace='hashivault-kv-oidc', name='HashiCorp Vault KV (OIDC)', inputs=oidc_type_inputs)
        oidc_type.save()
        yield oidc_type


@pytest.fixture
def oidc_credential(oidc_credentialtype):
    """Create a credential using the OIDC credential type."""
    return Credential.objects.create(
        credential_type=oidc_credentialtype,
        name='oidc-vault-cred',
        inputs={'url': 'http://vault.example.com:8200', 'auth_path': 'jwt', 'role_id': 'test-role', 'jwt_aud': 'vault'},
    )


@pytest.fixture
def mock_oidc_backend():
    """Fixture that mocks OIDC JWT generation and credential backend."""
    with mock.patch('awx.api.views.retrieve_workload_identity_jwt_with_claims') as mock_jwt, mock.patch('awx.api.views._jwt_decode') as mock_decode, mock.patch(
        'awx.main.models.credential.CredentialType.plugin', new_callable=mock.PropertyMock
    ) as mock_plugin:

        # Set default return values
        mock_jwt.return_value = 'fake.jwt.token'
        mock_decode.return_value = {'iss': 'http://gateway/o', 'aud': 'vault'}

        # Create mock backend
        mock_backend = mock.MagicMock()
        mock_backend.backend.return_value = 'secret'
        mock_plugin.return_value = mock_backend

        # Yield all mocks for test customization
        yield {
            'jwt': mock_jwt,
            'decode': mock_decode,
            'plugin': mock_plugin,
            'backend': mock_backend,
        }


# --- Tests for CredentialExternalTest endpoint ---


@pytest.mark.django_db
@override_settings(FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED=False)
def test_credential_test_without_oidc_feature_flag(post, admin, oidc_credential):
    """Test that credential test works without OIDC feature flag enabled."""
    url = reverse('api:credential_external_test', kwargs={'pk': oidc_credential.pk})
    data = {'metadata': {'secret_path': 'test/secret', 'job_template_id': '1'}}

    with mock.patch('awx.main.models.credential.CredentialType.plugin', new_callable=mock.PropertyMock) as mock_plugin:
        mock_backend = mock.MagicMock()
        mock_backend.backend.return_value = 'secret'
        mock_plugin.return_value = mock_backend

        response = post(url, data, admin)
        assert response.status_code == 202
        # Should not contain JWT payload when feature flag is disabled
        assert 'details' not in response.data or 'sent_jwt_payload' not in response.data.get('details', {})


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
@pytest.mark.parametrize(
    'job_template_id, expected_error',
    [
        (None, 'Job template ID is required'),
        ('not-an-integer', 'must be an integer'),
        ('99999', 'does not exist'),
    ],
    ids=['missing_job_template_id', 'invalid_job_template_id_type', 'nonexistent_job_template_id'],
)
def test_credential_test_job_template_validation(mock_flag, post, admin, oidc_credential, job_template_id, expected_error):
    """Test that invalid job_template_id values return 400 with appropriate error messages."""
    url = reverse('api:credential_external_test', kwargs={'pk': oidc_credential.pk})
    data = {'metadata': {'secret_path': 'test/secret'}}
    if job_template_id is not None:
        data['metadata']['job_template_id'] = job_template_id

    response = post(url, data, admin)
    assert response.status_code == 400
    assert 'details' in response.data
    assert 'error_message' in response.data['details']
    assert expected_error in response.data['details']['error_message']


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
def test_credential_test_no_access_to_job_template(mock_flag, post, alice, oidc_credential, job_template):
    """Test that user without access to job template gets 403."""
    url = reverse('api:credential_external_test', kwargs={'pk': oidc_credential.pk})
    data = {'metadata': {'secret_path': 'test/secret', 'job_template_id': str(job_template.id)}}

    # Give alice use permission on credential but not on job template
    oidc_credential.use_role.members.add(alice)

    response = post(url, data, alice)
    assert response.status_code == 403
    assert 'You do not have access to job template' in str(response.data)


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
def test_credential_test_success_returns_jwt_payload(mock_flag, post, admin, oidc_credential, job_template, mock_oidc_backend):
    """Test that successful test returns JWT payload in response."""
    url = reverse('api:credential_external_test', kwargs={'pk': oidc_credential.pk})
    data = {'metadata': {'secret_path': 'test/secret', 'job_template_id': str(job_template.id)}}

    # Customize mock for this test
    mock_oidc_backend['decode'].return_value = {
        'iss': 'http://gateway/o',
        'sub': 'system:serviceaccount:default:awx-operator',
        'aud': 'vault',
        'job_template_id': job_template.id,
    }

    response = post(url, data, admin)
    assert response.status_code == 202
    assert 'details' in response.data
    assert 'sent_jwt_payload' in response.data['details']
    assert response.data['details']['sent_jwt_payload']['job_template_id'] == job_template.id


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
def test_credential_test_backend_failure_returns_jwt_and_error(mock_flag, post, admin, oidc_credential, job_template, mock_oidc_backend):
    """Test that backend failure still returns JWT payload along with error message."""
    url = reverse('api:credential_external_test', kwargs={'pk': oidc_credential.pk})
    data = {'metadata': {'secret_path': 'test/secret', 'job_template_id': str(job_template.id)}}

    # Make backend fail
    mock_oidc_backend['backend'].backend.side_effect = RuntimeError('Connection failed')

    response = post(url, data, admin)
    assert response.status_code == 400
    assert 'details' in response.data
    # Both JWT payload and error message should be present
    assert 'sent_jwt_payload' in response.data['details']
    assert 'error_message' in response.data['details']
    assert 'Connection failed' in response.data['details']['error_message']


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
def test_credential_test_jwt_generation_failure(mock_flag, post, admin, oidc_credential, job_template):
    """Test that JWT generation failure returns error without JWT payload."""
    url = reverse('api:credential_external_test', kwargs={'pk': oidc_credential.pk})
    data = {'metadata': {'secret_path': 'test/secret', 'job_template_id': str(job_template.id)}}

    with mock.patch('awx.api.views.OIDCCredentialTestMixin._get_workload_identity_token') as mock_jwt:
        mock_jwt.side_effect = RuntimeError('Failed to generate JWT')

        response = post(url, data, admin)
        assert response.status_code == 400
        assert 'details' in response.data
        assert 'error_message' in response.data['details']
        assert 'Failed to generate JWT' in response.data['details']['error_message']
        # No JWT payload when generation fails
        assert 'sent_jwt_payload' not in response.data['details']


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
def test_credential_test_job_template_id_not_passed_to_backend(mock_flag, post, admin, oidc_credential, job_template, mock_oidc_backend):
    """Test that job_template_id and jwt_aud are removed from backend_kwargs."""
    url = reverse('api:credential_external_test', kwargs={'pk': oidc_credential.pk})
    data = {'metadata': {'secret_path': 'test/secret', 'job_template_id': str(job_template.id)}}

    response = post(url, data, admin)
    assert response.status_code == 202

    # Check that backend was called without job_template_id or jwt_aud
    call_kwargs = mock_oidc_backend['backend'].backend.call_args[1]
    assert 'job_template_id' not in call_kwargs
    assert 'jwt_aud' not in call_kwargs
    assert 'workload_identity_token' in call_kwargs


# --- Tests for CredentialTypeExternalTest endpoint ---


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
def test_credential_type_test_missing_job_template_id(mock_flag, post, admin, oidc_credentialtype):
    """Test that missing job_template_id returns 400 for credential type test endpoint."""
    url = reverse('api:credential_type_external_test', kwargs={'pk': oidc_credentialtype.pk})
    data = {
        'inputs': {'url': 'http://vault.example.com:8200', 'auth_path': 'jwt', 'role_id': 'test-role', 'jwt_aud': 'vault'},
        'metadata': {'secret_path': 'test/secret'},
    }

    response = post(url, data, admin)
    assert response.status_code == 400
    assert 'details' in response.data
    assert 'error_message' in response.data['details']
    assert 'Job template ID is required' in response.data['details']['error_message']


@pytest.mark.django_db
@mock.patch('awx.api.views.flag_enabled', return_value=True)
def test_credential_type_test_success_returns_jwt_payload(mock_flag, post, admin, oidc_credentialtype, job_template, mock_oidc_backend):
    """Test that successful credential type test returns JWT payload."""
    url = reverse('api:credential_type_external_test', kwargs={'pk': oidc_credentialtype.pk})
    data = {
        'inputs': {'url': 'http://vault.example.com:8200', 'auth_path': 'jwt', 'role_id': 'test-role', 'jwt_aud': 'vault'},
        'metadata': {'secret_path': 'test/secret', 'job_template_id': str(job_template.id)},
    }

    response = post(url, data, admin)
    assert response.status_code == 202
    assert 'details' in response.data
    assert 'sent_jwt_payload' in response.data['details']


@pytest.mark.django_db
def test_credential_external_test_returns_400_for_non_external_credential(post, admin, credential):
    # credential fixture creates a non-external credential (e.g. SSH/vault kind)
    url = reverse('api:credential_external_test', kwargs={'pk': credential.pk})
    response = post(url, {'metadata': {}}, admin)
    assert response.status_code == 400
    assert 'not testable' in response.data.get('detail', '').lower()
