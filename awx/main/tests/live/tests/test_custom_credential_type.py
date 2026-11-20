import pytest

from awx.main.models import CredentialType, Credential
from awx.main.tests.live.tests.conftest import unified_job_stdout


@pytest.fixture
def custom_cred_type(default_org):
    """Create a custom credential type that creates a file and sets an env var."""
    CredentialType.objects.filter(name='Custom File Type', kind='cloud').delete()

    cred_type = CredentialType(
        kind='cloud',
        name='Custom File Type',
        managed=False,
        inputs={
            'fields': [
                {
                    'id': 'test_file_content',
                    'label': 'File Content',
                    'type': 'string',
                    'required': True,
                }
            ]
        },
        injectors={'file': {'template.custom_file': '{{ test_file_content }}'}, 'env': {'CUSTOM_FILE_PATH': '{{ tower.filename.custom_file }}'}},
    )
    cred_type.save()
    return cred_type


@pytest.fixture
def custom_credential(custom_cred_type, default_org):
    """Create a credential using the custom type."""
    Credential.objects.filter(name='Custom File Credential').delete()

    cred = Credential(
        credential_type=custom_cred_type,
        name='Custom File Credential',
        organization=default_org,
        inputs={'test_file_content': 'Hello from custom credential type!'},
    )
    cred.save()
    return cred


def test_custom_credential_type_file_injection(
    run_job_from_playbook,
    live_tmp_folder,
    custom_credential,
):
    """
    Test that a custom credential type can inject files and environment variables.
    The playbook verifies that the injected file exists and contains the expected content,
    and that the environment variable points to the correct path.
    """
    result = run_job_from_playbook(
        test_name='custom_credential_type',
        playbook='test_cred.yml',
        scm_url=f'file://{live_tmp_folder}/custom_cred_project',
        credentials=[custom_credential],
    )

    job = result['job']
    assert job.status == 'successful', f'Job failed: {unified_job_stdout(job)}'
    output = unified_job_stdout(job)
    assert 'Hello from custom credential type!' in output


@pytest.fixture
def oci_cred_type(default_org):
    """Create an OCI-style credential type matching the customer's config from AAP-78106."""
    CredentialType.objects.filter(name='OCI Custom Credential', kind='cloud').delete()

    cred_type = CredentialType(
        kind='cloud',
        name='OCI Custom Credential',
        managed=False,
        inputs={
            'fields': [
                {'id': 'cred_oci_tenancy', 'type': 'string', 'label': 'Tenancy'},
                {'id': 'cred_oci_region', 'type': 'string', 'label': 'OCI Region'},
                {'id': 'cred_oci_user_id', 'type': 'string', 'label': 'OCI User Id'},
                {'id': 'cred_oci_fingerprint', 'type': 'string', 'label': 'OCI SSH Key Fingerprint'},
                {
                    'id': 'cred_oci_ssh_privkey',
                    'type': 'string',
                    'label': 'OCI SSH Key',
                    'format': 'ssh_private_key',
                    'secret': True,
                    'multiline': True,
                },
            ],
            'required': [
                'cred_oci_tenancy',
                'cred_oci_region',
                'cred_oci_fingerprint',
                'cred_oci_user_id',
            ],
        },
        injectors={
            'file': {
                'template.ssh_keyfile': '{{ cred_oci_ssh_privkey }}',
                'template.oci_dummy_config': (
                    '[DEFAULT]\n'
                    'user={{ cred_oci_user_id }}\n'
                    'fingerprint={{ cred_oci_fingerprint }}\n'
                    'tenancy={{ cred_oci_tenancy }}\n'
                    'region={{ cred_oci_region }}\n'
                    'key_file={{ tower.filename.ssh_keyfile }}'
                ),
            },
            'env': {
                'OCI_REGION': '{{ cred_oci_region }}',
                'OCI_TENANCY': '{{ cred_oci_tenancy }}',
                'OCI_USER_ID': '{{ cred_oci_user_id }}',
                'OCI_CONFIG_FILE': '{{ tower.filename.oci_dummy_config }}',
                'OCI_USER_KEY_FILE': '{{ tower.filename.ssh_keyfile }}',
                'OCI_USER_FINGERPRINT': '{{ cred_oci_fingerprint }}',
                'OCI_ANSIBLE_AUTH_TYPE': 'api_key',
            },
        },
    )
    cred_type.save()
    return cred_type


@pytest.fixture
def oci_credential(oci_cred_type, default_org):
    """Create a credential using the OCI credential type."""
    Credential.objects.filter(name='OCI Test Credential').delete()

    cred = Credential(
        credential_type=oci_cred_type,
        name='OCI Test Credential',
        organization=default_org,
        inputs={
            'cred_oci_tenancy': 'ocid1.tenancy.oc1..test',
            'cred_oci_region': 'us-ashburn-1',
            'cred_oci_user_id': 'ocid1.user.oc1..test',
            'cred_oci_fingerprint': 'aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99',
            'cred_oci_ssh_privkey': 'FAKE_OCI_PRIVATE_KEY_DATA',
        },
    )
    cred.save()
    return cred


def test_custom_credential_type_file_cross_reference(
    run_job_from_playbook,
    live_tmp_folder,
    oci_credential,
):
    """
    Test that a file template can reference another injected file's path via
    {{ tower.filename.ssh_keyfile }}. This mirrors the OCI credential type
    from AAP-78106 where oci_dummy_config contains key_file={{ tower.filename.ssh_keyfile }}.
    """
    result = run_job_from_playbook(
        test_name='custom_credential_type_cross_ref',
        playbook='test_cred_cross_ref.yml',
        scm_url=f'file://{live_tmp_folder}/custom_cred_project',
        credentials=[oci_credential],
    )

    job = result['job']
    assert job.status == 'successful', f'Job failed: {unified_job_stdout(job)}'
