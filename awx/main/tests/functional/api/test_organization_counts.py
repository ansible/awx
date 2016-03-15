import pytest

from django.core.urlresolvers import reverse

@pytest.fixture
def resourced_organization(organization, project, team, inventory, user):
    admin_user = user('test-admin', True)
    member_user = user('org-member')

    # Associate one resource of every type with the organization
    organization.users.add(member_user)
    organization.admins.add(admin_user)
    organization.projects.add(project)
    # organization.teams.create(name='org-team')
    # inventory = organization.inventories.create(name="associated-inv")
    project.jobtemplates.create(name="test-jt",
                                description="test-job-template-desc",
                                inventory=inventory,
                                playbook="test_playbook.yml")

    return organization

@pytest.mark.django_db
def test_org_counts_admin(resourced_organization, user, get):
    # Check that all types of resources are counted by a superuser
    external_admin = user('admin', True)
    response = get(reverse('api:organization_list', args=[]), external_admin)
    assert response.status_code == 200

    counts = response.data['results'][0]['summary_fields']['related_field_counts']
    assert counts == {
        'users': 1,
        'admins': 1,
        'job_templates': 1,
        'projects': 1,
        'inventories': 1,
        'teams': 1
    }

@pytest.mark.django_db
def test_org_counts_member(resourced_organization, get):
    # Check that a non-admin user can only see the full project and
    #   user count, consistent with the RBAC rules
    member_user = resourced_organization.users.get(username='org-member')
    response = get(reverse('api:organization_list', args=[]), member_user)
    assert response.status_code == 200

    counts = response.data['results'][0]['summary_fields']['related_field_counts']

    assert counts == {
        'users': 1,  # User can see themselves
        'admins': 0,
        'job_templates': 0,
        'projects': 1,  # Projects are shared with all the organization
        'inventories': 0,
        'teams': 0
    }

@pytest.mark.django_db
def test_new_org_zero_counts(user, post):
    # Check that a POST to the organization list endpoint returns
    #   correct counts, including the new record
    org_list_url = reverse('api:organization_list', args=[])
    post_response = post(url=org_list_url, data={'name': 'test organization',
                         'description': ''}, user=user('admin', True))
    assert post_response.status_code == 201

    new_org_list = post_response.render().data
    counts_dict = new_org_list['summary_fields']['related_field_counts']
    assert counts_dict == {
        'users': 0,
        'admins': 0,
        'job_templates': 0,
        'projects': 0,
        'inventories': 0,
        'teams': 0
    }

@pytest.mark.django_db
def test_two_organizations(resourced_organization, organizations, user, get):
    # Check correct results for two organizations are returned
    external_admin = user('admin', True)
    organization_zero = organizations(1)[0]
    response = get(reverse('api:organization_list', args=[]), external_admin)
    assert response.status_code == 200

    org_id_full = resourced_organization.id
    org_id_zero = organization_zero.id
    counts = {}
    for i in range(2):
        org_id = response.data['results'][i]['id']
        counts[org_id] = response.data['results'][i]['summary_fields']['related_field_counts']

    assert counts[org_id_full] == {
        'users': 1,
        'admins': 1,
        'job_templates': 1,
        'projects': 1,
        'inventories': 1,
        'teams': 1
    }
    assert counts[org_id_zero] == {
        'users': 0,
        'admins': 0,
        'job_templates': 0,
        'projects': 0,
        'inventories': 0,
        'teams': 0
    }

@pytest.mark.django_db
def test_JT_associated_with_project(organizations, project, user, get):
    # Check that adding a project to an organization gets the project's JT
    #  included in the organization's JT count
    external_admin = user('admin', True)
    two_orgs = organizations(2)
    organization = two_orgs[0]
    other_org = two_orgs[1]

    unrelated_inv = other_org.inventories.create(name='not-in-organization')
    project.jobtemplates.create(name="test-jt",
                                description="test-job-template-desc",
                                inventory=unrelated_inv,
                                playbook="test_playbook.yml")
    organization.projects.add(project)

    response = get(reverse('api:organization_list', args=[]), external_admin)
    assert response.status_code == 200

    org_id = organization.id
    counts = {}
    for i in range(2):
        working_id = response.data['results'][i]['id']
        counts[working_id] = response.data['results'][i]['summary_fields']['related_field_counts']

    assert counts[org_id] == {
        'users': 0,
        'admins': 0,
        'job_templates': 1,
        'projects': 1,
        'inventories': 0,
        'teams': 0
    }

