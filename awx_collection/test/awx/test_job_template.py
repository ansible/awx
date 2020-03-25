from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from awx.main.models import JobTemplate, Job


@pytest.mark.django_db
def test_create_job_template(run_module, admin_user, project, inventory):

    module_args = {
        'name': 'foo', 'playbook': 'helloworld.yml',
        'project': project.name, 'inventory': inventory.name,
        'extra_vars': {'foo': 'bar'},
        'job_type': 'run',
        'state': 'present'
    }

    result = run_module('tower_job_template', module_args, admin_user)

    jt = JobTemplate.objects.get(name='foo')
    assert jt.extra_vars == '{"foo": "bar"}'

    assert result == {
        "name": "foo",
        "created": True,
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
        ask_variables_on_launch=True,
        ask_inventory_on_launch=True,
        ask_credential_on_launch=True
    )
    result = run_module('tower_job_launch', dict(
        job_template='foo',
        inventory=inventory.name,
        credential=machine_credential.name,
        extra_vars={"var1": "My First Variable",
                    "var2": "My Second Variable",
                    "var3": "My Third Variable"
                    }
    ), admin_user)
    assert result.pop('changed', None), result

    job = Job.objects.get(id=result['id'])
    assert job.extra_vars == '{"var1": "My First Variable", "var2": "My Second Variable", "var3": "My Third Variable"}'
    assert job.inventory == inventory
    assert [cred.id for cred in job.credentials.all()] == [machine_credential.id]


@pytest.mark.django_db
def test_create_job_template_with_old_credentials(
        run_module, admin_user, project, inventory,
        machine_credential, vault_credential):

    module_args = {
        'name': 'foo', 'playbook': 'helloworld.yml',
        'project': project.name, 'inventory': inventory.name,
        'credential': machine_credential.name,
        'vault_credential': vault_credential.name,
        'job_type': 'run',
        'state': 'present'
    }

    result = run_module('tower_job_template', module_args, admin_user)

    jt = JobTemplate.objects.get(name='foo')

    result.pop("added_an_association")
    assert result == {
        "name": "foo",
        "id": jt.id,
        "created": True,
        "changed": True,
        "invocation": {
            "module_args": module_args
        }
    }

    assert set([machine_credential.id, vault_credential.id]) == set([
        cred.pk for cred in jt.credentials.all()])


@pytest.mark.django_db
def test_create_job_template_with_new_credentials(
        run_module, admin_user, project, inventory,
        machine_credential, vault_credential):
    jt = JobTemplate.objects.create(
        name='foo',
        playbook='helloworld.yml',
        inventory=inventory,
        project=project
    )
    result = run_module('tower_job_template', dict(
        name='foo',
        playbook='helloworld.yml',
        project=project.name,
        credentials=[machine_credential.name, vault_credential.name]
    ), admin_user)
    assert result.pop('changed', None), result

    result.pop('invocation')
    result.pop('added_an_association')
    result.pop('field_changes')
    assert result == {
        "updated": False,
        "needed_update": True,
        "id": jt.id
    }

    assert set([machine_credential.id, vault_credential.id]) == set([
        cred.pk for cred in jt.credentials.all()])
