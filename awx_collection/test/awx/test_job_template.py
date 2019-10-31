import pytest

from awx.main.models import JobTemplate, Job


@pytest.mark.django_db
def test_create_job_template(run_module, admin_user, project, inventory):

    module_args = {
        'name': 'foo', 'playbook': 'helloworld.yml',
        'project': project.name, 'inventory': inventory.name,
        'job_type': 'run',
        'state': 'present'
    }

    result = run_module('tower_job_template', module_args, admin_user)

    jt = JobTemplate.objects.get(name='foo')

    assert result == {
        "job_template": "foo",
        "state": "present",
        "id": jt.id,
        "changed": True,
        "invocation": {
            "module_args": module_args
        }
    }

    assert jt.project_id == project.id
    assert jt.inventory_id == inventory.id


@pytest.mark.django_db
def test_job_launch_with_prompting(run_module, admin_user, project, inventory, machine_credential):
    JobTemplate.objects.create(
        name='foo',
        project=project,
        playbook='helloworld.yml',
        ask_inventory_on_launch=True,
        ask_credential_on_launch=True
    )
    result = run_module('tower_job_launch', dict(
        job_template='foo',
        inventory=inventory.name,
        credential=machine_credential.name
    ), admin_user)
    assert result.pop('changed', None), result

    job = Job.objects.get(id=result['id'])
    assert job.inventory == inventory
    assert [cred.id for cred in job.credentials.all()] == [machine_credential.id]


@pytest.mark.django_db
def test_create_job_template_with_old_machine_cred(run_module, admin_user, project, inventory, machine_credential):

    module_args = {
        'name': 'foo', 'playbook': 'helloworld.yml',
        'project': project.name, 'inventory': inventory.name, 'credential': machine_credential.name,
        'job_type': 'run',
        'state': 'present'
    }

    result = run_module('tower_job_template', module_args, admin_user)

    jt = JobTemplate.objects.get(name='foo')

    assert result == {
        "job_template": "foo",
        "state": "present",
        "id": jt.id,
        "changed": True,
        "invocation": {
            "module_args": module_args
        }
    }

    assert machine_credential.id in [cred.pk for cred in jt.credentials.all()]
