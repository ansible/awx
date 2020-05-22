from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json

from awx.main.models import (
    Organization,
    Project,
    Inventory,
    Host,
    CredentialType,
    Credential,
    JobTemplate
)


# warns based on password_management param, but not security issue
@pytest.mark.django_db
def test_receive_send_jt(run_module, admin_user, mocker, silence_deprecation):
    org = Organization.objects.create(name='SRtest')
    proj = Project.objects.create(
        name='SRtest',
        playbook_files=['debug.yml'],
        scm_type='git',
        scm_url='https://github.com/ansible/test-playbooks.git',
        organization=org,
        allow_override=True  # so we do not require playbooks populated
    )
    inv = Inventory.objects.create(name='SRtest', organization=org)
    Host.objects.create(name='SRtest', inventory=inv)
    ct = CredentialType.defaults['ssh']()
    ct.save()
    cred = Credential.objects.create(
        name='SRtest',
        credential_type=ct,
        organization=org
    )
    jt = JobTemplate.objects.create(
        name='SRtest',
        project=proj,
        inventory=inv,
        playbook='helloworld.yml'
    )
    jt.credentials.add(cred)
    jt.admin_role.members.add(admin_user)  # work around send/receive bug

    # receive everything
    result = run_module('tower_receive', dict(all=True), admin_user)

    assert 'assets' in result, result
    assets = result['assets']
    assert not result.get('changed', True)
    assert set(a['asset_type'] for a in assets) == set((
        'organization', 'inventory', 'job_template', 'credential', 'project',
        'user'
    ))

    # delete everything
    for obj in (jt, inv, proj, cred, org):
        obj.delete()

    def fake_wait(self, pk, parent_pk=None, **kwargs):
        return {"changed": True}

    # recreate everything
    with mocker.patch('sys.stdin.isatty', return_value=True):
        with mocker.patch('tower_cli.models.base.MonitorableResource.wait'):
            result = run_module('tower_send', dict(assets=json.dumps(assets)), admin_user)

    assert not result.get('failed'), result

    new = JobTemplate.objects.get(name='SRtest')
    assert new.project.name == 'SRtest'
    assert new.inventory.name == 'SRtest'
    assert [cred.name for cred in new.credentials.all()] == ['SRtest']
