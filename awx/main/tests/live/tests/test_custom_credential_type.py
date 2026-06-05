import pytest

from awx.api.versioning import reverse
from awx.main.models import CredentialType, Credential, JobTemplate
from awx.main.tests.live.tests.conftest import unified_job_stdout, wait_for_job


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
        injectors={
            'file': {'template.custom_file': '{{ test_file_content }}'},
            'env': {'CUSTOM_FILE_PATH': '{{ tower.filename.custom_file }}'},
        },
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
    project_factory,
    demo_inv,
    live_tmp_folder,
    custom_credential,
    post,
    admin,
):
    """
    Test that a custom credential type can inject files and environment variables.
    The playbook verifies that the injected file exists and contains the expected content,
    and that the environment variable points to the correct path.
    """
    proj = project_factory(scm_url=f'file://{live_tmp_folder}/custom_cred_project')

    if proj.current_job:
        wait_for_job(proj.current_job)

    playbook = 'test_cred.yml'
    assert proj.get_project_path()
    assert playbook in proj.playbooks

    jt_name = 'custom_credential_type JT: test_cred.yml'
    JobTemplate.objects.filter(name=jt_name).delete()

    result = post(
        reverse('api:job_template_list'),
        {'name': jt_name, 'project': proj.id, 'playbook': playbook, 'inventory': demo_inv.id},
        admin,
        expect=201,
    )
    jt = JobTemplate.objects.get(id=result.data['id'])

    jt.credentials.add(custom_credential)

    job = jt.create_unified_job()
    job.signal_start()
    wait_for_job(job)

    assert job.status == 'successful', f'Job failed: {unified_job_stdout(job)}'
    output = unified_job_stdout(job)
    assert 'Hello from custom credential type!' in output
