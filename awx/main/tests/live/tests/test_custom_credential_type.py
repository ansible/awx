import pytest

from awx.main.models import CredentialType, Credential
from awx.main.tests.live.tests.conftest import unified_job_stdout


@pytest.fixture
def simple_file_cred_type(default_org):
    """Create a custom credential type that creates a single file with multiline content."""
    CredentialType.objects.filter(name='Simple File Type', kind='cloud').delete()

    cred_type = CredentialType(
        kind='cloud',
        name='Simple File Type',
        managed=False,
        inputs={
            'fields': [
                {
                    'id': 'file_content',
                    'label': 'File Content',
                    'type': 'string',
                    'required': True,
                }
            ]
        },
        injectors={'file': {'template.config': '{{ file_content }}'}, 'env': {'CONFIG_FILE_PATH': '{{ tower.filename.config }}'}},
    )
    cred_type.save()
    return cred_type


@pytest.fixture
def simple_file_credential(simple_file_cred_type, default_org):
    """Create a credential using the simple file type."""
    Credential.objects.filter(name='Simple File Credential').delete()

    file_content = '''[main]
host=localhost
port=8080
debug=true'''

    cred = Credential(
        credential_type=simple_file_cred_type,
        name='Simple File Credential',
        organization=default_org,
        inputs={'file_content': file_content},
    )
    cred.save()
    return cred


@pytest.fixture
def cross_ref_cred_type(default_org):
    """Create a custom credential type with two files where one references the other."""
    CredentialType.objects.filter(name='Cross Ref File Type', kind='cloud').delete()

    cred_type = CredentialType(
        kind='cloud',
        name='Cross Ref File Type',
        managed=False,
        inputs={
            'fields': [
                {
                    'id': 'config_content',
                    'label': 'Config Content',
                    'type': 'string',
                    'required': True,
                },
                {
                    'id': 'extra_content',
                    'label': 'Extra Content',
                    'type': 'string',
                    'required': True,
                },
            ]
        },
        injectors={
            'file': {'template.config': '{{ config_content }}', 'template.extra': '{{ extra_content }}'},
            'env': {'CONFIG_FILE_PATH': '{{ tower.filename.config }}', 'EXTRA_FILE_PATH': '{{ tower.filename.extra }}'},
        },
    )
    cred_type.save()
    return cred_type


@pytest.fixture
def cross_ref_credential(cross_ref_cred_type, default_org):
    """Create a credential using the cross-reference type with two files."""
    Credential.objects.filter(name='Cross Ref Credential').delete()

    config_content = '''[main]
host=localhost
port=8080
debug=true'''

    extra_content = '''Config file location: {{ tower.filename.config }}
Additional settings for the configuration.
Created by custom credential injection.'''

    cred = Credential(
        credential_type=cross_ref_cred_type,
        name='Cross Ref Credential',
        organization=default_org,
        inputs={'config_content': config_content, 'extra_content': extra_content},
    )
    cred.save()
    return cred


def test_custom_credential_type_single_file_injection(
    run_job_from_playbook,
    live_tmp_folder,
    simple_file_credential,
):
    """
    Test that a custom credential type can inject a single file with multiline content
    and set an environment variable pointing to it.
    """
    result = run_job_from_playbook(
        test_name='simple_file_injection',
        playbook='test_cred.yml',
        scm_url=f'file://{live_tmp_folder}/custom_cred_project',
        credentials=[simple_file_credential],
    )

    job = result['job']
    assert job.status == 'successful', f'Job failed: {unified_job_stdout(job)}'
    output = unified_job_stdout(job)
    # Verify file was created and accessible with multiline content
    assert 'localhost' in output
    assert 'port=8080' in output


def test_custom_credential_type_cross_file_references(
    run_job_from_playbook,
    live_tmp_folder,
    cross_ref_credential,
):
    """
    Test that a custom credential type can inject multiple files where one file
    references another using tower.filename.xyz syntax, and environment variables
    properly expose the injected file paths.
    """
    result = run_job_from_playbook(
        test_name='cross_ref_injection',
        playbook='test_cred.yml',
        scm_url=f'file://{live_tmp_folder}/custom_cred_project',
        credentials=[cross_ref_credential],
    )

    job = result['job']
    assert job.status == 'successful', f'Job failed: {unified_job_stdout(job)}'
    output = unified_job_stdout(job)
    # Verify both files were created and accessible
    assert 'localhost' in output  # From config file
    assert 'Additional settings' in output  # From extra file
    assert 'Created by custom credential injection' in output
