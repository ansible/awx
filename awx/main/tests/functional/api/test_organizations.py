# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import os

from backports.tempfile import TemporaryDirectory
from django.conf import settings
import pytest

# AWX
from awx.main.models import ProjectUpdate, CredentialType, Credential
from awx.api.versioning import reverse


@pytest.fixture
def create_job_factory(job_factory, project):
    def fn(status='running'):
        j = job_factory()
        j.status = status
        j.project = project
        j.save()
        return j
    return fn


@pytest.fixture
def create_project_update_factory(organization, project):
    def fn(status='running'):
        pu = ProjectUpdate(project=project)
        pu.status = status
        pu.organization = organization
        pu.save()
        return pu
    return fn


@pytest.fixture
def organization_jobs_successful(create_job_factory, create_project_update_factory):
    return [create_job_factory(status='successful') for i in range(0, 2)] + \
        [create_project_update_factory(status='successful') for i in range(0, 2)]


@pytest.fixture
def organization_jobs_running(create_job_factory, create_project_update_factory):
    return [create_job_factory(status='running') for i in range(0, 2)] + \
        [create_project_update_factory(status='running') for i in range(0, 2)]


@pytest.mark.django_db
def test_organization_list_access_tests(options, head, get, admin, alice):
    options(reverse('api:organization_list'), user=admin, expect=200)
    head(reverse('api:organization_list'), user=admin, expect=200)
    get(reverse('api:organization_list'), user=admin, expect=200)
    options(reverse('api:organization_list'), user=alice, expect=200)
    head(reverse('api:organization_list'), user=alice, expect=200)
    get(reverse('api:organization_list'), user=alice, expect=200)
    options(reverse('api:organization_list'), user=None, expect=401)
    head(reverse('api:organization_list'), user=None, expect=401)
    get(reverse('api:organization_list'), user=None, expect=401)


@pytest.mark.django_db
def test_organization_access_tests(organization, get, admin, alice, bob):
    organization.member_role.members.add(alice)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=admin, expect=200)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=200)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=bob, expect=403)
    get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=None, expect=401)


@pytest.mark.django_db
def test_organization_list_integrity(organization, get, admin, alice):
    res = get(reverse('api:organization_list'), user=admin)
    for field in ['id', 'url', 'name', 'description', 'created']:
        assert field in res.data['results'][0]


@pytest.mark.django_db
def test_organization_list_visibility(organizations, get, admin, alice):
    orgs = organizations(2)

    res = get(reverse('api:organization_list'), user=admin)
    assert res.data['count'] == 2
    assert len(res.data['results']) == 2

    res = get(reverse('api:organization_list'), user=alice)
    assert res.data['count'] == 0

    orgs[1].member_role.members.add(alice)

    res = get(reverse('api:organization_list'), user=alice)
    assert res.data['count'] == 1
    assert len(res.data['results']) == 1
    assert res.data['results'][0]['id'] == orgs[1].id


@pytest.mark.django_db
def test_organization_project_list(organization, project_factory, get, alice, bob, rando):
    prj1 = project_factory('project-one')
    project_factory('project-two')
    organization.admin_role.members.add(alice)
    organization.member_role.members.add(bob)
    prj1.use_role.members.add(bob)
    assert get(reverse('api:organization_projects_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 2
    assert get(reverse('api:organization_projects_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 1
    assert get(reverse('api:organization_projects_list', kwargs={'pk': organization.id}), user=rando).status_code == 403


@pytest.mark.django_db
def test_organization_user_list(organization, get, admin, alice, bob):
    organization.admin_role.members.add(alice)
    organization.member_role.members.add(alice)
    organization.member_role.members.add(bob)
    assert get(reverse('api:organization_users_list', kwargs={'pk': organization.id}), user=admin).data['count'] == 2
    assert get(reverse('api:organization_users_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 2
    assert get(reverse('api:organization_users_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 2
    assert get(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), user=admin).data['count'] == 1
    assert get(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 1
    assert get(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 1


@pytest.mark.django_db
def test_organization_inventory_list(organization, inventory_factory, get, alice, bob, rando):
    inv1 = inventory_factory('inventory-one')
    inventory_factory('inventory-two')
    organization.admin_role.members.add(alice)
    organization.member_role.members.add(bob)
    inv1.use_role.members.add(bob)
    assert get(reverse('api:organization_inventories_list', kwargs={'pk': organization.id}), user=alice).data['count'] == 2
    assert get(reverse('api:organization_inventories_list', kwargs={'pk': organization.id}), user=bob).data['count'] == 1
    get(reverse('api:organization_inventories_list', kwargs={'pk': organization.id}), user=rando, expect=403)


@pytest.mark.django_db
def test_create_organization(post, admin, alice):
    new_org = {
        'name': 'new org',
        'description': 'my description'
    }
    res = post(reverse('api:organization_list'), new_org, user=admin, expect=201)
    assert res.data['name'] == new_org['name']
    res = post(reverse('api:organization_list'), new_org, user=admin, expect=400)


@pytest.mark.django_db
def test_create_organization_xfail(post, alice):
    new_org = {
        'name': 'new org',
        'description': 'my description'
    }
    post(reverse('api:organization_list'), new_org, user=alice, expect=403)


@pytest.mark.django_db
def test_add_user_to_organization(post, organization, alice, bob):
    organization.admin_role.members.add(alice)
    post(reverse('api:organization_users_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=204)
    assert bob in organization.member_role
    post(reverse('api:organization_users_list', kwargs={'pk': organization.id}), {'id': bob.id, 'disassociate': True} , user=alice, expect=204)
    assert bob not in organization.member_role


@pytest.mark.django_db
def test_add_user_to_organization_xfail(post, organization, alice, bob):
    organization.member_role.members.add(alice)
    post(reverse('api:organization_users_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=403)


@pytest.mark.django_db
def test_add_admin_to_organization(post, organization, alice, bob):
    organization.admin_role.members.add(alice)
    post(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=204)
    assert bob in organization.admin_role
    assert bob in organization.member_role
    post(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), {'id': bob.id, 'disassociate': True} , user=alice, expect=204)
    assert bob not in organization.admin_role
    assert bob not in organization.member_role


@pytest.mark.django_db
def test_add_admin_to_organization_xfail(post, organization, alice, bob):
    organization.member_role.members.add(alice)
    post(reverse('api:organization_admins_list', kwargs={'pk': organization.id}), {'id': bob.id}, user=alice, expect=403)


@pytest.mark.django_db
def test_update_organization(get, put, organization, alice, bob):
    organization.admin_role.members.add(alice)
    data = get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=200).data
    data['description'] = 'hi'
    put(reverse('api:organization_detail', kwargs={'pk': organization.id}), data, user=alice, expect=200)
    organization.refresh_from_db()
    assert organization.description == 'hi'
    data['description'] = 'bye'
    put(reverse('api:organization_detail', kwargs={'pk': organization.id}), data, user=bob, expect=403)


@pytest.mark.django_db
def test_update_organization_max_hosts(get, put, organization, admin, alice, bob):
    # Admin users can get and update max_hosts
    data = get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=admin, expect=200).data
    assert organization.max_hosts == 0
    data['max_hosts'] = 3
    put(reverse('api:organization_detail', kwargs={'pk': organization.id}), data, user=admin, expect=200)
    organization.refresh_from_db()
    assert organization.max_hosts == 3

    # Organization admins can get the data and can update other fields, but not max_hosts
    organization.admin_role.members.add(alice)
    data = get(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=200).data
    data['max_hosts'] = 5
    put(reverse('api:organization_detail', kwargs={'pk': organization.id}), data, user=alice, expect=400)
    organization.refresh_from_db()
    assert organization.max_hosts == 3

    # Ordinary users shouldn't be able to update either.
    put(reverse('api:organization_detail', kwargs={'pk': organization.id}), data, user=bob, expect=403)
    organization.refresh_from_db()
    assert organization.max_hosts == 3


@pytest.mark.django_db
def test_delete_organization(delete, organization, admin):
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=admin, expect=204)


@pytest.mark.django_db
def test_delete_organization2(delete, organization, alice):
    organization.admin_role.members.add(alice)
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=204)


@pytest.mark.django_db
def test_delete_organization_xfail1(delete, organization, alice):
    organization.member_role.members.add(alice)
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=alice, expect=403)


@pytest.mark.django_db
def test_delete_organization_xfail2(delete, organization):
    delete(reverse('api:organization_detail', kwargs={'pk': organization.id}), user=None, expect=401)


@pytest.mark.django_db
def test_organization_custom_virtualenv(get, patch, organization, admin):
    with TemporaryDirectory(dir=settings.BASE_VENV_PATH) as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'bin', 'activate'))
        url = reverse('api:organization_detail', kwargs={'pk': organization.id})
        patch(url, {'custom_virtualenv': temp_dir}, user=admin, expect=200)
        assert get(url, user=admin).data['custom_virtualenv'] == os.path.join(temp_dir, '')


@pytest.mark.django_db
def test_organization_invalid_custom_virtualenv(get, patch, organization, admin):
    url = reverse('api:organization_detail', kwargs={'pk': organization.id})
    resp = patch(url, {'custom_virtualenv': '/foo/bar'}, user=admin, expect=400)
    assert resp.data['custom_virtualenv'] == [
        '/foo/bar is not a valid virtualenv in {}'.format(settings.BASE_VENV_PATH)
    ]


@pytest.mark.django_db
@pytest.mark.parametrize('value', ["", None])
def test_organization_unset_custom_virtualenv(get, patch, organization, admin, value):
    url = reverse('api:organization_detail', kwargs={'pk': organization.id})
    resp = patch(url, {'custom_virtualenv': value}, user=admin, expect=200)
    assert resp.data['custom_virtualenv'] is None


@pytest.mark.django_db
def test_organization_delete(delete, admin, organization, organization_jobs_successful):
    url = reverse('api:organization_detail', kwargs={'pk': organization.id})
    delete(url, None, user=admin, expect=204)


@pytest.mark.django_db
def test_organization_delete_with_active_jobs(delete, admin, organization, organization_jobs_running):
    def sort_keys(x):
        return (x['type'], str(x['id']))

    url = reverse('api:organization_detail', kwargs={'pk': organization.id})
    resp = delete(url, None, user=admin, expect=409)

    expect_transformed = [dict(id=j.id, type=j.model_to_str()) for j in organization_jobs_running]
    resp_sorted = sorted(resp.data['active_jobs'], key=sort_keys)
    expect_sorted = sorted(expect_transformed, key=sort_keys)

    assert resp.data['error'] == u"Resource is being used by running jobs."
    assert resp_sorted == expect_sorted


@pytest.mark.django_db
def test_galaxy_credential_association_forbidden(alice, organization, post):
    galaxy = CredentialType.defaults['galaxy_api_token']()
    galaxy.save()

    cred = Credential.objects.create(
        credential_type=galaxy,
        name='Public Galaxy',
        organization=organization,
        inputs={
            'url': 'https://galaxy.ansible.com/'
        }
    )
    url = reverse('api:organization_galaxy_credentials_list', kwargs={'pk': organization.id})
    post(
        url,
        {'associate': True, 'id': cred.pk},
        user=alice,
        expect=403
    )


@pytest.mark.django_db
def test_galaxy_credential_type_enforcement(admin, organization, post):
    ssh = CredentialType.defaults['ssh']()
    ssh.save()

    cred = Credential.objects.create(
        credential_type=ssh,
        name='SSH Credential',
        organization=organization,
    )
    url = reverse('api:organization_galaxy_credentials_list', kwargs={'pk': organization.id})
    resp = post(
        url,
        {'associate': True, 'id': cred.pk},
        user=admin,
        expect=400
    )
    assert resp.data['msg'] == 'Credential must be a Galaxy credential, not Machine.'


@pytest.mark.django_db
def test_galaxy_credential_association(alice, admin, organization, post, get):
    galaxy = CredentialType.defaults['galaxy_api_token']()
    galaxy.save()

    for i in range(5):
        cred = Credential.objects.create(
            credential_type=galaxy,
            name=f'Public Galaxy {i + 1}',
            organization=organization,
            inputs={
                'url': 'https://galaxy.ansible.com/'
            }
        )
        url = reverse('api:organization_galaxy_credentials_list', kwargs={'pk': organization.id})
        post(
            url,
            {'associate': True, 'id': cred.pk},
            user=admin,
            expect=204
        )
    resp = get(url, user=admin)
    assert [cred['name'] for cred in resp.data['results']] == [
        'Public Galaxy 1',
        'Public Galaxy 2',
        'Public Galaxy 3',
        'Public Galaxy 4',
        'Public Galaxy 5',
    ]

    post(
        url,
        {'disassociate': True, 'id': Credential.objects.get(name='Public Galaxy 3').pk},
        user=admin,
        expect=204
    )
    resp = get(url, user=admin)
    assert [cred['name'] for cred in resp.data['results']] == [
        'Public Galaxy 1',
        'Public Galaxy 2',
        'Public Galaxy 4',
        'Public Galaxy 5',
    ]
