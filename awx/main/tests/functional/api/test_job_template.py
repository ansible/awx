import os

from backports.tempfile import TemporaryDirectory
import pytest

# AWX
from awx.api.serializers import JobTemplateSerializer
from awx.api.versioning import reverse
from awx.main.models import Job, JobTemplate, CredentialType, WorkflowJobTemplate
from awx.main.migrations import _save_password_keys as save_password_keys

# Django
from django.conf import settings
from django.apps import apps

# DRF
from rest_framework.exceptions import ValidationError


@pytest.mark.django_db
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

    r = post(reverse('api:job_template_list'), {
        'name': 'Some name',
        'project': project.id,
        'credential': machine_credential.id,  # TODO: remove in 3.3
        'inventory': inventory.id,
        'playbook': 'helloworld.yml',
    }, alice)
    if expect == 201:
        jt = JobTemplate.objects.get(id=r.data['id'])
        assert set(jt.credentials.values_list('id', flat=True)) == set([machine_credential.id])
    assert r.status_code == expect


# TODO: remove in 3.3
@pytest.mark.django_db
def test_create_with_v1_deprecated_credentials(get, post, project, machine_credential, credential, net_credential, inventory, alice):
    project.use_role.members.add(alice)
    machine_credential.use_role.members.add(alice)
    credential.use_role.members.add(alice)
    net_credential.use_role.members.add(alice)
    inventory.use_role.members.add(alice)

    pk = post(reverse('api:job_template_list', kwargs={'version': 'v1'}), {
        'name': 'Some name',
        'project': project.id,
        'credential': machine_credential.id,
        'cloud_credential': credential.id,
        'network_credential': net_credential.id,
        'inventory': inventory.id,
        'playbook': 'helloworld.yml',
    }, alice, expect=201).data['id']

    url = reverse('api:job_template_detail', kwargs={'version': 'v1', 'pk': pk})
    response = get(url, alice)
    assert response.data.get('cloud_credential') == credential.pk
    assert response.data.get('network_credential') == net_credential.pk


# TODO: remove in 3.3
@pytest.mark.django_db
def test_create_with_empty_v1_deprecated_credentials(get, post, project, machine_credential, inventory, alice):
    project.use_role.members.add(alice)
    machine_credential.use_role.members.add(alice)
    inventory.use_role.members.add(alice)

    pk = post(reverse('api:job_template_list', kwargs={'version': 'v1'}), {
        'name': 'Some name',
        'project': project.id,
        'credential': machine_credential.id,
        'cloud_credential': None,
        'network_credential': None,
        'inventory': inventory.id,
        'playbook': 'helloworld.yml',
    }, alice, expect=201).data['id']

    url = reverse('api:job_template_detail', kwargs={'version': 'v1', 'pk': pk})
    response = get(url, alice)
    assert response.data.get('cloud_credential') is None
    assert response.data.get('network_credential') is None


# TODO: remove in 3.3
@pytest.mark.django_db
def test_create_v1_rbac_check(get, post, project, credential, net_credential, rando):
    project.use_role.members.add(rando)

    base_kwargs = dict(
        name = 'Made with cloud/net creds I have no access to',
        project = project.id,
        ask_inventory_on_launch = True,
        ask_credential_on_launch = True,
        playbook = 'helloworld.yml',
    )

    base_kwargs['cloud_credential'] = credential.pk
    post(reverse('api:job_template_list', kwargs={'version': 'v1'}), base_kwargs, rando, expect=403)

    base_kwargs.pop('cloud_credential')
    base_kwargs['network_credential'] = net_credential.pk
    post(reverse('api:job_template_list', kwargs={'version': 'v1'}), base_kwargs, rando, expect=403)


# TODO: remove as each field tested has support removed
@pytest.mark.django_db
def test_jt_deprecated_summary_fields(
        project, inventory,
        machine_credential, net_credential, vault_credential,
        mocker):
    jt = JobTemplate.objects.create(
        project=project,
        inventory=inventory,
        playbook='helloworld.yml'
    )

    class MockView:
        kwargs = {}
        request = None

    class MockRequest:
        version = 'v1'
        user = None

    view = MockView()
    request = MockRequest()
    view.request = request
    serializer = JobTemplateSerializer(instance=jt, context={'view': view, 'request': request})

    for kwargs in [{}, {'pk': 1}]:  # detail vs. list view
        for version in ['v1', 'v2']:
            view.kwargs = kwargs
            request.version = version
            sf = serializer.get_summary_fields(jt)
            assert 'credential' not in sf
            assert 'vault_credential' not in sf

    jt.credentials.add(machine_credential, net_credential, vault_credential)

    view.kwargs = {'pk': 1}
    for version in ['v1', 'v2']:
        request.version = version
        sf = serializer.get_summary_fields(jt)
        assert 'credential' in sf
        assert sf['credential']  # not empty dict
        assert 'vault_credential' in sf
        assert sf['vault_credential']


@pytest.mark.django_db
def test_extra_credential_creation(get, post, organization_factory, job_template_factory, credentialtype_aws):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    url = reverse('api:job_template_extra_credentials_list', kwargs={'version': 'v2', 'pk': jt.pk})
    response = post(url, {
        'name': 'My Cred',
        'credential_type': credentialtype_aws.pk,
        'inputs': {
            'username': 'bob',
            'password': 'secret',
        }
    }, objs.superusers.admin)
    assert response.status_code == 201

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1


@pytest.mark.django_db
@pytest.mark.parametrize('kind', ['scm', 'insights'])
def test_invalid_credential_kind_xfail(get, post, organization_factory, job_template_factory, kind):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    url = reverse('api:job_template_credentials_list', kwargs={'version': 'v2', 'pk': jt.pk})
    cred_type = CredentialType.defaults[kind]()
    cred_type.save()
    response = post(url, {
        'name': 'My Cred',
        'credential_type': cred_type.pk,
        'inputs': {
            'username': 'bob',
            'password': 'secret',
        }
    }, objs.superusers.admin, expect=400)
    assert 'Cannot assign a Credential of kind `{}`.'.format(kind) in response.data.values()


@pytest.mark.django_db
def test_extra_credential_unique_type_xfail(get, post, organization_factory, job_template_factory, credentialtype_aws):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    url = reverse('api:job_template_extra_credentials_list', kwargs={'version': 'v2', 'pk': jt.pk})
    response = post(url, {
        'name': 'My Cred',
        'credential_type': credentialtype_aws.pk,
        'inputs': {
            'username': 'bob',
            'password': 'secret',
        }
    }, objs.superusers.admin)
    assert response.status_code == 201

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1

    # this request should fail because you can't assign the same type (aws)
    # twice
    response = post(url, {
        'name': 'My Cred',
        'credential_type': credentialtype_aws.pk,
        'inputs': {
            'username': 'joe',
            'password': 'another-secret',
        }
    }, objs.superusers.admin)
    assert response.status_code == 400

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1


@pytest.mark.django_db
def test_attach_extra_credential(get, post, organization_factory, job_template_factory, credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    url = reverse('api:job_template_extra_credentials_list', kwargs={'version': 'v2', 'pk': jt.pk})
    response = post(url, {
        'associate': True,
        'id': credential.id,
    }, objs.superusers.admin)
    assert response.status_code == 204

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 1


@pytest.mark.django_db
def test_detach_extra_credential(get, post, organization_factory, job_template_factory, credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.credentials.add(credential)
    jt.save()

    url = reverse('api:job_template_extra_credentials_list', kwargs={'version': 'v2', 'pk': jt.pk})
    response = post(url, {
        'disassociate': True,
        'id': credential.id,
    }, objs.superusers.admin)
    assert response.status_code == 204

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 0


@pytest.mark.django_db
def test_attach_extra_credential_wrong_kind_xfail(get, post, organization_factory, job_template_factory, machine_credential):
    """Extra credentials only allow net + cloud credentials"""
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    url = reverse('api:job_template_extra_credentials_list', kwargs={'version': 'v2', 'pk': jt.pk})
    response = post(url, {
        'associate': True,
        'id': machine_credential.id,
    }, objs.superusers.admin)
    assert response.status_code == 400

    response = get(url, user=objs.superusers.admin)
    assert response.data.get('count') == 0


# TODO: remove in 3.3
@pytest.mark.django_db
def test_v1_extra_credentials_detail(get, organization_factory, job_template_factory, credential, net_credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.credentials.add(credential)
    jt.credentials.add(net_credential)
    jt.save()

    url = reverse('api:job_template_detail', kwargs={'version': 'v1', 'pk': jt.pk})
    response = get(url, user=objs.superusers.admin)
    assert response.data.get('cloud_credential') == credential.pk
    assert response.data.get('network_credential') == net_credential.pk


# TODO: remove in 3.3
@pytest.mark.django_db
def test_v1_set_extra_credentials_assignment(get, patch, organization_factory, job_template_factory, credential, net_credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.save()

    url = reverse('api:job_template_detail', kwargs={'version': 'v1', 'pk': jt.pk})
    response = patch(url, {
        'cloud_credential': credential.pk,
        'network_credential': net_credential.pk
    }, objs.superusers.admin)
    assert response.status_code == 200

    url = reverse('api:job_template_detail', kwargs={'version': 'v1', 'pk': jt.pk})
    response = get(url, user=objs.superusers.admin)
    assert response.status_code == 200
    assert response.data.get('cloud_credential') == credential.pk
    assert response.data.get('network_credential') == net_credential.pk

    url = reverse('api:job_template_detail', kwargs={'version': 'v1', 'pk': jt.pk})
    response = patch(url, {
        'cloud_credential': None,
        'network_credential': None,
    }, objs.superusers.admin)
    assert response.status_code == 200

    url = reverse('api:job_template_detail', kwargs={'version': 'v1', 'pk': jt.pk})
    response = get(url, user=objs.superusers.admin)
    assert response.status_code == 200
    assert response.data.get('cloud_credential') is None
    assert response.data.get('network_credential') is None


@pytest.mark.django_db
def test_filter_by_v1(get, organization_factory, job_template_factory, credential, net_credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.credentials.add(credential)
    jt.credentials.add(net_credential)
    jt.save()

    for query in (
        ('cloud_credential', str(credential.pk)),
        ('network_credential', str(net_credential.pk))
    ):
        url = reverse('api:job_template_list', kwargs={'version': 'v1'})
        response = get(
            url,
            user=objs.superusers.admin,
            QUERY_STRING='='.join(query)
        )
        assert response.data.get('count') == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "grant_project, grant_inventory, expect", [
        (True, True, 200),
        (True, False, 403),
        (False, True, 403),
    ]
)
def test_edit_sensitive_fields(patch, job_template_factory, alice, grant_project, grant_inventory, expect):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    objs.job_template.admin_role.members.add(alice)

    if grant_project:
        objs.project.use_role.members.add(alice)
    if grant_inventory:
        objs.inventory.use_role.members.add(alice)

    patch(url=reverse('api:job_template_detail', kwargs={'pk': objs.job_template.id}), data={
        'name': 'Some name',
        'project': objs.project.id,
        'inventory': objs.inventory.id,
        'playbook': 'alt-helloworld.yml',
    }, user=alice, expect=expect)


@pytest.mark.django_db
def test_reject_dict_extra_vars_patch(patch, job_template_factory, admin_user):
    # Expect a string for extra_vars, raise 400 in this case that would
    # otherwise have been saved incorrectly
    jt = job_template_factory(
        'jt', organization='org1', project='prj', inventory='inv', credential='cred'
    ).job_template
    patch(reverse('api:job_template_detail', kwargs={'pk': jt.id}),
          {'extra_vars': {'foo': 5}}, admin_user, expect=400)


@pytest.mark.django_db
def test_edit_playbook(patch, job_template_factory, alice):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    objs.job_template.admin_role.members.add(alice)
    objs.project.use_role.members.add(alice)
    objs.credential.use_role.members.add(alice)
    objs.inventory.use_role.members.add(alice)

    patch(reverse('api:job_template_detail', kwargs={'pk': objs.job_template.id}), {
        'playbook': 'alt-helloworld.yml',
    }, alice, expect=200)

    objs.inventory.use_role.members.remove(alice)
    patch(reverse('api:job_template_detail', kwargs={'pk': objs.job_template.id}), {
        'playbook': 'helloworld.yml',
    }, alice, expect=403)


@pytest.mark.django_db
@pytest.mark.parametrize('json_body',
                         ["abc", True, False, "{\"name\": \"test\"}", 100, .5])
def test_invalid_json_body(patch, job_template_factory, alice, json_body):
    objs = job_template_factory('jt', organization='org1')
    objs.job_template.admin_role.members.add(alice)
    resp = patch(
        reverse('api:job_template_detail', kwargs={'pk': objs.job_template.id}),
        json_body,
        alice,
        expect=400
    )
    assert resp.data['detail'] == (
        u'JSON parse error - not a JSON object'
    )


@pytest.mark.django_db
def test_edit_nonsenstive(patch, job_template_factory, alice):
    objs = job_template_factory('jt', organization='org1', project='prj', inventory='inv', credential='cred')
    jt = objs.job_template
    jt.admin_role.members.add(alice)

    res = patch(reverse('api:job_template_detail', kwargs={'pk': jt.id}), {
        'name': 'updated',
        'description': 'bar',
        'forks': 14,
        'limit': 'something',
        'verbosity': 5,
        'extra_vars': '---',
        'job_tags': 'sometags',
        'force_handlers': True,
        'skip_tags': 'thistag,thattag',
        'ask_variables_on_launch':True,
        'ask_tags_on_launch':True,
        'ask_skip_tags_on_launch':True,
        'ask_job_type_on_launch':True,
        'ask_inventory_on_launch':True,
        'ask_credential_on_launch': True,
    }, alice, expect=200)
    assert res.data['name'] == 'updated'


@pytest.fixture
def jt_copy_edit(job_template_factory, project):
    objects = job_template_factory(
        'copy-edit-job-template',
        project=project)
    return objects.job_template


@pytest.mark.django_db
def test_job_template_role_user(post, organization_factory, job_template_factory):
    objects = organization_factory("org",
                                   superusers=['admin'],
                                   users=['test'])

    jt_objects = job_template_factory("jt",
                                      organization=objects.organization,
                                      inventory='test_inv',
                                      project='test_proj')

    url = reverse('api:user_roles_list', kwargs={'pk': objects.users.test.pk})
    response = post(url, dict(id=jt_objects.job_template.execute_role.pk), objects.superusers.admin)
    assert response.status_code == 204


@pytest.mark.django_db
def test_jt_admin_copy_edit_functional(jt_copy_edit, rando, get, post):
    # Grant random user JT admin access only
    jt_copy_edit.admin_role.members.add(rando)
    jt_copy_edit.save()

    get_response = get(reverse('api:job_template_detail', kwargs={'pk':jt_copy_edit.pk}), user=rando)
    assert get_response.status_code == 200

    post_data = get_response.data
    post_data['name'] = '%s @ 12:19:47 pm' % post_data['name']
    post_response = post(reverse('api:job_template_list'), user=rando, data=post_data)
    assert post_response.status_code == 403


@pytest.mark.django_db
def test_launch_with_pending_deletion_inventory(get, post, organization_factory,
                                                job_template_factory, machine_credential,
                                                credential, net_credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization, credential='c',
                              inventory='test_inv', project='test_proj').job_template
    jt.inventory.pending_deletion = True
    jt.inventory.save()

    resp = post(
        reverse('api:job_template_launch', kwargs={'pk': jt.pk}),
        objs.superusers.admin, expect=400
    )
    assert resp.data['inventory'] == ['The inventory associated with this Job Template is being deleted.']


@pytest.mark.django_db
def test_launch_with_pending_deletion_inventory_workflow(get, post, organization, inventory, admin_user):
    wfjt = WorkflowJobTemplate.objects.create(
        name='wfjt',
        organization=organization,
        inventory=inventory
    )

    inventory.pending_deletion = True
    inventory.save()

    resp = post(
        url=reverse('api:workflow_job_template_launch', kwargs={'pk': wfjt.pk}),
        user=admin_user, expect=400
    )
    assert resp.data['inventory'] == ['The inventory associated with this Workflow is being deleted.']


@pytest.mark.django_db
def test_launch_with_extra_credentials(get, post, organization_factory,
                                       job_template_factory, machine_credential,
                                       credential, net_credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.ask_credential_on_launch = True
    jt.save()

    resp = post(
        reverse('api:job_template_launch', kwargs={'pk': jt.pk}),
        dict(
            credentials=[machine_credential.pk, credential.pk, net_credential.pk]
        ),
        objs.superusers.admin, expect=201
    )
    job_pk = resp.data.get('id')

    resp = get(reverse('api:job_extra_credentials_list', kwargs={'pk': job_pk}), objs.superusers.admin)
    assert resp.data.get('count') == 2

    resp = get(reverse('api:job_template_extra_credentials_list', kwargs={'pk': jt.pk}), objs.superusers.admin)
    assert resp.data.get('count') == 0


@pytest.mark.django_db
def test_launch_with_extra_credentials_not_allowed(get, post, organization_factory,
                                                   job_template_factory, machine_credential,
                                                   credential, net_credential):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.credentials.add(machine_credential)
    jt.ask_credential_on_launch = False
    jt.save()

    resp = post(
        reverse('api:job_template_launch', kwargs={'pk': jt.pk}),
        dict(
            credentials=[machine_credential.pk, credential.pk, net_credential.pk]
        ),
        objs.superusers.admin
    )
    assert 'credentials' in resp.data['ignored_fields'].keys()
    job_pk = resp.data.get('id')

    resp = get(reverse('api:job_extra_credentials_list', kwargs={'pk': job_pk}), objs.superusers.admin)
    assert resp.data.get('count') == 0


@pytest.mark.django_db
def test_v1_launch_with_extra_credentials(get, post, organization_factory,
                                          job_template_factory, machine_credential,
                                          credential, net_credential):
    # launch requests to `/api/v1/job_templates/N/launch/` should ignore
    # `extra_credentials`, as they're only supported in v2 of the API.
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template
    jt.ask_credential_on_launch = True
    jt.save()

    resp = post(
        reverse('api:job_template_launch', kwargs={'pk': jt.pk, 'version': 'v1'}),
        dict(
            credential=machine_credential.pk,
            extra_credentials=[credential.pk, net_credential.pk]
        ),
        objs.superusers.admin, expect=400
    )
    assert 'Field is not allowed for use with v1 API' in resp.data.get('extra_credentials')


@pytest.mark.django_db
def test_jt_without_project(inventory):
    data = dict(name="Test", job_type="run",
                inventory=inventory.pk, project=None)
    serializer = JobTemplateSerializer(data=data)
    assert not serializer.is_valid()
    assert "project" in serializer.errors
    data["job_type"] = "check"
    serializer = JobTemplateSerializer(data=data)
    assert not serializer.is_valid()
    assert "project" in serializer.errors


@pytest.mark.django_db
def test_disallow_template_delete_on_running_job(job_template_factory, delete, admin_user):
    objects = job_template_factory('jt',
                                   credential='c',
                                   job_type="run",
                                   project='p',
                                   inventory='i',
                                   organization='o')
    objects.job_template.create_unified_job()
    delete_response = delete(reverse('api:job_template_detail', kwargs={'pk': objects.job_template.pk}), user=admin_user)
    assert delete_response.status_code == 409


@pytest.mark.django_db
def test_save_survey_passwords_to_job(job_template_with_survey_passwords):
    """Test that when a new job is created, the survey_passwords field is
    given all of the passwords that exist in the JT survey"""
    job = job_template_with_survey_passwords.create_unified_job()
    assert job.survey_passwords == {'SSN': '$encrypted$', 'secret_key': '$encrypted$'}


@pytest.mark.django_db
def test_save_survey_passwords_on_migration(job_template_with_survey_passwords):
    """Test that when upgrading to 3.0.2, the jobs connected to a JT that has
    a survey with passwords in it, the survey passwords get saved to the
    job survey_passwords field."""
    Job.objects.create(job_template=job_template_with_survey_passwords)
    save_password_keys.migrate_survey_passwords(apps, None)
    job = job_template_with_survey_passwords.jobs.all()[0]
    assert job.survey_passwords == {'SSN': '$encrypted$', 'secret_key': '$encrypted$'}


@pytest.mark.django_db
@pytest.mark.parametrize('access', ["superuser", "admin", "peon"])
def test_job_template_custom_virtualenv(get, patch, organization_factory, job_template_factory, alice, access):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    user = alice
    if access == "superuser":
        user = objs.superusers.admin
    elif access == "admin":
        jt.admin_role.members.add(alice)
    else:
        jt.read_role.members.add(alice)

    with TemporaryDirectory(dir=settings.BASE_VENV_PATH) as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'bin', 'activate'))
        url = reverse('api:job_template_detail', kwargs={'pk': jt.id})

        if access == "peon":
            patch(url, {'custom_virtualenv': temp_dir}, user=user, expect=403)
            assert 'custom_virtualenv' not in get(url, user=user)
            assert JobTemplate.objects.get(pk=jt.id).custom_virtualenv is None
        else:
            patch(url, {'custom_virtualenv': temp_dir}, user=user, expect=200)
            assert get(url, user=user).data['custom_virtualenv'] == os.path.join(temp_dir, '')


@pytest.mark.django_db
def test_job_template_invalid_custom_virtualenv(get, patch, organization_factory,
                                                job_template_factory):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    url = reverse('api:job_template_detail', kwargs={'pk': jt.id})
    resp = patch(url, {'custom_virtualenv': '/foo/bar'}, user=objs.superusers.admin, expect=400)
    assert resp.data['custom_virtualenv'] == [
        '/foo/bar is not a valid virtualenv in {}'.format(settings.BASE_VENV_PATH)
    ]


@pytest.mark.django_db
@pytest.mark.parametrize('value', ["", None])
def test_job_template_unset_custom_virtualenv(get, patch, organization_factory,
                                              job_template_factory, value):
    objs = organization_factory("org", superusers=['admin'])
    jt = job_template_factory("jt", organization=objs.organization,
                              inventory='test_inv', project='test_proj').job_template

    url = reverse('api:job_template_detail', kwargs={'pk': jt.id})
    resp = patch(url, {'custom_virtualenv': value}, user=objs.superusers.admin, expect=200)
    assert resp.data['custom_virtualenv'] is None


@pytest.mark.django_db
def test_callback_disallowed_null_inventory(project):
    jt = JobTemplate.objects.create(
        name='test-jt', inventory=None,
        ask_inventory_on_launch=True,
        project=project, playbook='helloworld.yml')
    serializer = JobTemplateSerializer(jt)
    assert serializer.instance == jt
    with pytest.raises(ValidationError) as exc:
        serializer.validate({'host_config_key': 'asdfbasecfeee'})
    assert 'Cannot enable provisioning callback without an inventory set' in str(exc)
