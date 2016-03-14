import pytest

from django.core.urlresolvers import reverse

@pytest.fixture
def resourced_organization(organization, project, user):
    admin_user = user('test-admin', True)
    member_user = user('org-member')

    # Associate one resource of every type with the organization
    organization.users.add(member_user)
    organization.admins.add(admin_user)
    organization.projects.add(project)
    organization.teams.create(name='org-team')
    inventory = organization.inventories.create(name="associated-inv")
    inventory.jobtemplates.create(name="test-jt",
                                  description="test-job-template-desc",
                                  project=project,
                                  playbook="test_playbook.yml")

    return organization

@pytest.mark.django_db
def test_org_counts_admin(resourced_organization, user, get):
    # Check that all types of resources are counted by a superuser
    external_admin = user('admin', True)
    response = get(reverse('api:organization_list', args=[]), external_admin)
    counts = response.data['results'][0]['summary_fields']['counts']

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
    counts = response.data['results'][0]['summary_fields']['counts']

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
    new_org_list = post_response.render().data
    counts_dict = new_org_list['summary_fields']['counts']

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
    org_id_full = resourced_organization.id
    org_id_zero = organization_zero.id
    print ' ids: ' + str(org_id_full) + " : " + str(org_id_zero)
    print ' counts_dict: ' + str(response.data['results'])
    counts = {}
    for i in range(2):
        org_id = response.data['results'][i]['id']
        counts[org_id] = response.data['results'][i]['summary_fields']['counts']

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
