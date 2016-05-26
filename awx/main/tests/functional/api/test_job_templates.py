import mock # noqa
import pytest
from awx.main.models.projects import ProjectOptions


from django.core.urlresolvers import reverse

def decorators(func):
    @property
    def project_playbooks(self):
        return ['mocked', 'othermocked']

    return pytest.mark.django_db(mock.patch.object(ProjectOptions, "playbooks", project_playbooks)(func))

@decorators
@pytest.mark.parametrize(
    "grant_project, grant_credential, grant_inventory, expect", [
        (True, True, True, 201),
        (True, True, False, 403),
        (True, False, True, 403),
        (False, True, True, 403),
    ]
)
def test_create(post, project, machine_credential, inventory, alice, grant_project, grant_credential, grant_inventory, expect):
    if grant_project:
        project.use_role.members.add(alice)
    if grant_credential:
        machine_credential.use_role.members.add(alice)
    if grant_inventory:
        inventory.use_role.members.add(alice)

    post(reverse('api:job_template_list'), {
        'name': 'Some name',
        'project': project.id,
        'credential': machine_credential.id,
        'inventory': inventory.id,
        'playbook': 'mocked',
    }, alice, expect=expect)

@decorators
@pytest.mark.parametrize(
    "grant_project, grant_credential, grant_inventory, expect", [
        (True, True, True, 200),
        (True, True, False, 403),
        (True, False, True, 403),
        (False, True, True, 403),
    ]
)
def test_edit_sensitive_fields(patch, job_template_factory, alice, grant_project, grant_credential, grant_inventory, expect):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    objs.job_template.admin_role.members.add(alice)

    if grant_project:
        objs.project.use_role.members.add(alice)
    if grant_credential:
        objs.credential.use_role.members.add(alice)
    if grant_inventory:
        objs.inventory.use_role.members.add(alice)

    patch(reverse('api:job_template_detail', args=(objs.job_template.id,)), {
        'name': 'Some name',
        'project': objs.project.id,
        'credential': objs.credential.id,
        'inventory': objs.inventory.id,
        'playbook': 'othermocked',
    }, alice, expect=expect)

@decorators
def test_edit_playbook(patch, job_template_factory, alice):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    objs.job_template.admin_role.members.add(alice)
    objs.project.use_role.members.add(alice)
    objs.credential.use_role.members.add(alice)
    objs.inventory.use_role.members.add(alice)

    patch(reverse('api:job_template_detail', args=(objs.job_template.id,)), {
        'playbook': 'othermocked',
    }, alice, expect=200)

    objs.inventory.use_role.members.remove(alice)
    patch(reverse('api:job_template_detail', args=(objs.job_template.id,)), {
        'playbook': 'mocked',
    }, alice, expect=403)

@decorators
def test_edit_nonsenstive(patch, job_template_factory, alice):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    jt = objs.job_template
    jt.admin_role.members.add(alice)

    res = patch(reverse('api:job_template_detail', args=(jt.id,)), {
        'name': 'updated',
        'description': 'bar',
        'forks': 14,
        'limit': 'something',
        'verbosity': 5,
        'extra_vars': '--',
        'job_tags': 'sometags',
        'force_handlers': True,
        'skip_tags': True,
        'ask_variables_on_launch':True,
        'ask_tags_on_launch':True,
        'ask_job_type_on_launch':True,
        'ask_inventory_on_launch':True,
        'ask_credential_on_launch': True,
        'survey_enabled':True,
    }, alice, expect=200)
    print(res.data)
    assert res.data['name'] == 'updated'
