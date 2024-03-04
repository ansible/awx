from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.main.models.execution_environments import ExecutionEnvironment
from awx.main.models.jobs import JobTemplate

from awx.main.tests.functional.conftest import user, system_auditor  # noqa: F401; pylint: disable=unused-import


ASSETS = set([
    "users",
    "organizations",
    "teams",
    "credential_types",
    "credentials",
    "notification_templates",
    "projects",
    "inventory",
    "inventory_sources",
    "job_templates",
    "workflow_job_templates",
    "execution_environments",
    "applications",
    "schedules",
])


@pytest.fixture
def job_template(project, inventory, organization, machine_credential):
    jt = JobTemplate.objects.create(name='test-jt', project=project, inventory=inventory, organization=organization, playbook='helloworld.yml')
    jt.credentials.add(machine_credential)
    jt.save()
    return jt


@pytest.fixture
def execution_environment(organization):
    return ExecutionEnvironment.objects.create(name="test-ee", description="test-ee", managed=False, organization=organization)


def find_by(result, name, key, value):
    for c in result[name]:
        if c[key] == value:
            return c
    values = [c.get(key, None) for c in result[name]]
    raise ValueError(f"Failed to find assets['{name}'][{key}] = '{value}' valid values are {values}")


@pytest.mark.django_db
def test_export(run_module, admin_user):
    """
    There should be nothing to export EXCEPT the admin user.
    """
    result = run_module('export', dict(all=True), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assets = result['assets']

    assert set(result['assets'].keys()) == ASSETS

    u = find_by(assets, 'users', 'username', 'admin')
    assert u['is_superuser'] is True

    all_assets_except_users = {k: v for k, v in assets.items() if k != 'users'}

    for k, v in all_assets_except_users.items():
        assert v == [], f"Expected resource {k} to be empty. Instead it is {v}"


@pytest.mark.django_db
def test_export_simple(
    run_module,
    organization,
    project,
    inventory,
    job_template,
    scm_credential,
    machine_credential,
    workflow_job_template,
    execution_environment,
    notification_template,
    rrule,
    schedule,
    admin_user,
):
    """
    TODO: Ensure there aren't _more_ results in each resource than we expect
    """
    result = run_module('export', dict(all=True), admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    assets = result['assets']

    u = find_by(assets, 'users', 'username', 'admin')
    assert u['is_superuser'] is True

    find_by(assets, 'organizations', 'name', 'Default')

    r = find_by(assets, 'credentials', 'name', 'scm-cred')
    assert r['credential_type']['kind'] == 'scm'
    assert r['credential_type']['name'] == 'Source Control'

    r = find_by(assets, 'credentials', 'name', 'machine-cred')
    assert r['credential_type']['kind'] == 'ssh'
    assert r['credential_type']['name'] == 'Machine'

    r = find_by(assets, 'job_templates', 'name', 'test-jt')
    assert r['natural_key']['organization']['name'] == 'Default'
    assert r['inventory']['name'] == 'test-inv'
    assert r['project']['name'] == 'test-proj'

    find_by(r['related'], 'credentials', 'name', 'machine-cred')

    r = find_by(assets, 'inventory', 'name', 'test-inv')
    assert r['organization']['name'] == 'Default'

    r = find_by(assets, 'projects', 'name', 'test-proj')
    assert r['organization']['name'] == 'Default'

    r = find_by(assets, 'workflow_job_templates', 'name', 'test-workflow_job_template')
    assert r['natural_key']['organization']['name'] == 'Default'
    assert r['inventory']['name'] == 'test-inv'

    r = find_by(assets, 'execution_environments', 'name', 'test-ee')
    assert r['organization']['name'] == 'Default'

    r = find_by(assets, 'schedules', 'name', 'test-sched')
    assert r['rrule'] == rrule

    r = find_by(assets, 'notification_templates', 'name', 'test-notification_template')
    assert r['organization']['name'] == 'Default'
    assert r['notification_configuration']['url'] == 'http://localhost'


@pytest.mark.django_db
def test_export_system_auditor(run_module, organization, system_auditor):  # noqa: F811
    """
    This test illustrates that export of resources can now happen
    when ran as non-root user (i.e. system auditor). The OPTIONS
    endpoint does NOT return POST for a system auditor, but now we
    make a best-effort to parse the description string, which will
    often have the fields.
    """
    result = run_module('export', dict(all=True), system_auditor)
    assert not result.get('failed', False), result.get('msg', result)
    assert 'msg' not in result
    assert 'assets' in result

    find_by(result['assets'], 'organizations', 'name', 'Default')
