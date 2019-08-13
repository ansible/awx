import pytest

from awx.api.versioning import reverse

from awx.main.models import Project


@pytest.fixture
def organization_resource_creator(organization, user):
    def rf(users, admins, job_templates, projects, inventories, teams):

        # Associate one resource of every type with the organization
        for i in range(users):
            member_user = user('org-member %s' % i)
            organization.member_role.members.add(member_user)
        for i in range(admins):
            admin_user = user('org-admin %s' % i)
            organization.admin_role.members.add(admin_user)
        for i in range(teams):
            organization.teams.create(name='org-team %s' % i)
        for i in range(inventories):
            inventory = organization.inventories.create(name="associated-inv %s" % i)
        for i in range(projects):
            Project.objects.create(
                name="test-proj %s" % i,
                description="test-proj-desc",
                organization=organization
            )
        # Mix up the inventories and projects used by the job templates
        i_proj = 0
        i_inv = 0
        for i in range(job_templates):
            project = Project.objects.filter(organization=organization)[i_proj]
            # project = organization.projects.all()[i_proj]
            inventory = organization.inventories.all()[i_inv]
            project.jobtemplates.create(name="test-jt %s" % i,
                                        description="test-job-template-desc",
                                        inventory=inventory,
                                        playbook="test_playbook.yml",
                                        organization=organization)
            i_proj += 1
            i_inv += 1
            if i_proj >= Project.objects.filter(organization=organization).count():
                i_proj = 0
            if i_inv >= organization.inventories.count():
                i_inv = 0

        return organization
    return rf


COUNTS_PRIMES = {
    'users': 11,
    'admins': 5,
    'job_templates': 3,
    'projects': 3,
    'inventories': 7,
    'teams': 5
}
COUNTS_ZEROS = {
    'users': 0,
    'admins': 0,
    'job_templates': 0,
    'projects': 0,
    'inventories': 0,
    'teams': 0
}


@pytest.fixture
def resourced_organization(organization_resource_creator):
    return organization_resource_creator(**COUNTS_PRIMES)


@pytest.mark.django_db
def test_org_counts_detail_admin(resourced_organization, user, get):
    # Check that all types of resources are counted by a superuser
    external_admin = user('admin', True)
    response = get(reverse('api:organization_detail',
                   kwargs={'pk': resourced_organization.pk}), external_admin)
    assert response.status_code == 200

    counts = response.data['summary_fields']['related_field_counts']
    assert counts == COUNTS_PRIMES


@pytest.mark.django_db
def test_org_counts_detail_member(resourced_organization, user, get):
    # Check that a non-admin org member can only see users / admin in detail view
    member_user = resourced_organization.member_role.members.get(username='org-member 1')
    response = get(reverse('api:organization_detail',
                   kwargs={'pk': resourced_organization.pk}), member_user)
    assert response.status_code == 200

    counts = response.data['summary_fields']['related_field_counts']
    assert counts == {
        'users': COUNTS_PRIMES['users'],  # Policy is that members can see other users and admins
        'admins': COUNTS_PRIMES['admins'],
        'job_templates': 0,
        'projects': 0,
        'inventories': 0,
        'teams': 0
    }


@pytest.mark.django_db
def test_org_counts_list_admin(resourced_organization, user, get):
    # Check that all types of resources are counted by a superuser
    external_admin = user('admin', True)
    response = get(reverse('api:organization_list'), external_admin)
    assert response.status_code == 200

    counts = response.data['results'][0]['summary_fields']['related_field_counts']
    assert counts == COUNTS_PRIMES


@pytest.mark.django_db
def test_org_counts_list_member(resourced_organization, user, get):
    # Check that a non-admin user can only see the full project and
    #   user count, consistent with the RBAC rules
    member_user = resourced_organization.member_role.members.get(username='org-member 1')
    response = get(reverse('api:organization_list'), member_user)
    assert response.status_code == 200

    counts = response.data['results'][0]['summary_fields']['related_field_counts']

    assert counts == {
        'users': COUNTS_PRIMES['users'],  # Policy is that members can see other users and admins
        'admins': COUNTS_PRIMES['admins'],
        'job_templates': 0,
        'projects': 0,
        'inventories': 0,
        'teams': 0
    }


@pytest.mark.django_db
def test_new_org_zero_counts(user, post):
    # Check that a POST to the organization list endpoint returns
    #   correct counts, including the new record
    org_list_url = reverse('api:organization_list')
    post_response = post(url=org_list_url, data={'name': 'test organization',
                         'description': ''}, user=user('admin', True))
    assert post_response.status_code == 201

    new_org_list = post_response.render().data
    counts_dict = new_org_list['summary_fields']['related_field_counts']
    assert counts_dict == COUNTS_ZEROS


@pytest.mark.django_db
def test_two_organizations(resourced_organization, organizations, user, get):
    # Check correct results for two organizations are returned
    external_admin = user('admin', True)
    organization_zero = organizations(1)[0]
    response = get(reverse('api:organization_list'), external_admin)
    assert response.status_code == 200

    org_id_full = resourced_organization.id
    org_id_zero = organization_zero.id
    counts = {}
    for i in range(2):
        org_id = response.data['results'][i]['id']
        counts[org_id] = response.data['results'][i]['summary_fields']['related_field_counts']

    assert counts[org_id_full] == COUNTS_PRIMES
    assert counts[org_id_zero] == COUNTS_ZEROS


@pytest.mark.django_db
def test_scan_JT_counted(resourced_organization, user, get):
    admin_user = user('admin', True)
    counts_dict = COUNTS_PRIMES

    # Test list view
    list_response = get(reverse('api:organization_list'), admin_user)
    assert list_response.status_code == 200
    assert list_response.data['results'][0]['summary_fields']['related_field_counts'] == counts_dict

    # Test detail view
    detail_response = get(reverse('api:organization_detail', kwargs={'pk': resourced_organization.pk}), admin_user)
    assert detail_response.status_code == 200
    assert detail_response.data['summary_fields']['related_field_counts'] == counts_dict


@pytest.mark.django_db
def test_JT_not_double_counted(resourced_organization, user, get):
    admin_user = user('admin', True)
    proj = Project.objects.filter(organization=resourced_organization).all()[0]
    # Add a run job template to the org
    proj.jobtemplates.create(
        job_type='run',
        inventory=resourced_organization.inventories.all()[0],
        project=proj,
        name='double-linked-job-template',
        organization=resourced_organization)
    counts_dict = COUNTS_PRIMES
    counts_dict['job_templates'] += 1

    # Test list view
    list_response = get(reverse('api:organization_list'), admin_user)
    assert list_response.status_code == 200
    assert list_response.data['results'][0]['summary_fields']['related_field_counts'] == counts_dict

    # Test detail view
    detail_response = get(reverse('api:organization_detail', kwargs={'pk': resourced_organization.pk}), admin_user)
    assert detail_response.status_code == 200
    assert detail_response.data['summary_fields']['related_field_counts'] == counts_dict
