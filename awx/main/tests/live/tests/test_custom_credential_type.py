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
