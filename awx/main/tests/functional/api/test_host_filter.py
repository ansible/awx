import pytest
import urllib.parse

from awx.api.versioning import reverse

from awx.main.models import Organization, Host, Group, Inventory, Job, JobEvent


@pytest.fixture
def inventory_structure():
    org = Organization.objects.create(name="org")
    inv = Inventory.objects.create(name="inv", organization=org)
    Host.objects.create(name="host1", inventory=inv)
    Host.objects.create(name="host2", inventory=inv)
    Host.objects.create(name="host3", inventory=inv)
    Group.objects.create(name="g1", inventory=inv)
    Group.objects.create(name="g2", inventory=inv)
    Group.objects.create(name="g3", inventory=inv)


@pytest.fixture
def host_filter_inventory():
    """Inventory with hosts and groups matching the tower-qa test_host_filter structure.

    Groups: groupA (contains groupAA as child), groupAA, groupB
    Hosts: hostA (in groupA), hostAA (in groupAA), hostB (in groupB), hostDup (in all 3 groups)
    """
    org = Organization.objects.create(name="hf-org")
    inv = Inventory.objects.create(name="hf-inv", organization=org)

    groupA = Group.objects.create(name="groupA", inventory=inv)
    groupAA = Group.objects.create(name="groupAA", inventory=inv)
    groupB = Group.objects.create(name="groupB", inventory=inv)

    hostA = Host.objects.create(name="hostA", inventory=inv)
    hostAA = Host.objects.create(name="hostAA", inventory=inv)
    hostB = Host.objects.create(name="hostB", inventory=inv)
    hostDup = Host.objects.create(name="hostDup", inventory=inv)

    groupA.hosts.add(hostA, hostDup)
    groupAA.hosts.add(hostAA, hostDup)
    groupB.hosts.add(hostB, hostDup)
    groupA.children.add(groupAA)

    return {
        'org': org,
        'inv': inv,
        'hosts': {'hostA': hostA, 'hostAA': hostAA, 'hostB': hostB, 'hostDup': hostDup},
        'groups': {'groupA': groupA, 'groupAA': groupAA, 'groupB': groupB},
    }


def get_host_names(response):
    return sorted(h['name'] for h in response.data['results'])


def host_filter_get(get, user, host_filter):
    url = reverse('api:host_list')
    params = "?host_filter=%s" % urllib.parse.quote(host_filter, safe='')
    return get(url + params, user)


@pytest.mark.django_db
def test_q1(inventory_structure, get, user):
    def evaluate_query(query, expected_hosts):
        url = reverse('api:host_list')
        get_params = "?host_filter=%s" % urllib.parse.quote(query, safe='')
        response = get(url + get_params, user('admin', True))

        hosts = response.data['results']

        assert len(expected_hosts) == len(hosts)

        host_ids = [host['id'] for host in hosts]
        for i, expected_host in enumerate(expected_hosts):
            assert expected_host.id in host_ids

    hosts = Host.objects.all()
    groups = Group.objects.all()

    groups[0].hosts.add(hosts[0], hosts[1])
    groups[1].hosts.add(hosts[0], hosts[1], hosts[2])

    query = '(name="host1" and groups__name="g1")'
    evaluate_query(query, [hosts[0]])

    query = '(name="host1" and groups__name="g1") or (name="host3" and groups__name="g2")'
    evaluate_query(query, [hosts[0], hosts[2]])

    # The following test verifies if the search in host_filter is case insensitive.
    query = 'search="HOST1"'
    evaluate_query(query, [hosts[0]])


# --- Host filter query tests (migrated from tower-qa test_host_filter.py) ---


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host_filter, expected",
    [
        ("name=hostA", ["hostA"]),
        ("name=not_found", []),
        ("name=hostDup", ["hostDup"]),
    ],
)
def test_basic_host_name_search(host_filter_inventory, get, admin_user, host_filter, expected):
    response = host_filter_get(get, admin_user, host_filter)
    assert response.status_code == 200
    assert get_host_names(response) == sorted(expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host_filter, expected",
    [
        ("name=hostA or name=hostB", ["hostA", "hostB"]),
        ("name=hostA or name=not_found", ["hostA"]),
        ("name=not_found or name=not_found", []),
        ("name=hostA or name=hostA", ["hostA"]),
        ("name=hostDup or name=hostDup", ["hostDup"]),
        ("name=hostA or name=hostAA or name=not_found", ["hostA", "hostAA"]),
    ],
)
def test_host_name_search_with_or(host_filter_inventory, get, admin_user, host_filter, expected):
    response = host_filter_get(get, admin_user, host_filter)
    assert response.status_code == 200
    assert get_host_names(response) == sorted(expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host_filter, expected",
    [
        ("name=hostA and name=hostB", []),
        ("name=hostA and name=hostA", ["hostA"]),
        ("name=not_found and name=not_found", []),
        ("name=hostDup and name=hostDup", ["hostDup"]),
        ("name=hostA and name=hostB and name=not_found", []),
    ],
)
def test_host_name_search_with_and(host_filter_inventory, get, admin_user, host_filter, expected):
    response = host_filter_get(get, admin_user, host_filter)
    assert response.status_code == 200
    assert get_host_names(response) == sorted(expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host_filter, expected",
    [
        ("groups__name=groupA", ["hostA", "hostDup"]),
        ("groups__name=groupAA", ["hostAA", "hostDup"]),
        ("groups__name=not_found", []),
    ],
)
def test_basic_group_search(host_filter_inventory, get, admin_user, host_filter, expected):
    response = host_filter_get(get, admin_user, host_filter)
    assert response.status_code == 200
    assert get_host_names(response) == sorted(expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host_filter, expected",
    [
        ("groups__name=groupA or groups__name=groupB", ["hostA", "hostB", "hostDup"]),
        ("groups__name=groupA or groups__name=not_found", ["hostA", "hostDup"]),
        ("groups__name=not_found or groups__name=not_found", []),
        ("groups__name=groupA or groups__name=groupA", ["hostA", "hostDup"]),
        (
            "groups__name=groupA or groups__name=groupAA or groups__name=not_found",
            ["hostA", "hostAA", "hostDup"],
        ),
    ],
)
def test_group_search_with_or(host_filter_inventory, get, admin_user, host_filter, expected):
    response = host_filter_get(get, admin_user, host_filter)
    assert response.status_code == 200
    assert get_host_names(response) == sorted(expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host_filter, expected",
    [
        ("groups__name=groupA and groups__name=groupB", ["hostDup"]),
        ("groups__name=groupA and groups__name=groupA", ["hostA", "hostDup"]),
        ("groups__name=not_found and groups__name=not_found", []),
        ("groups__name=groupA and groups__name=groupB and groups__name=not_found", []),
    ],
)
def test_group_search_with_and(host_filter_inventory, get, admin_user, host_filter, expected):
    response = host_filter_get(get, admin_user, host_filter)
    assert response.status_code == 200
    assert get_host_names(response) == sorted(expected)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "host_filter, expected",
    [
        ("name=hostA or groups__name=groupB", ["hostA", "hostB", "hostDup"]),
        ("name=hostA and groups__name=groupA", ["hostA"]),
        ("name=hostA and groups__name=not_found", []),
        ("name=not_found and groups__name=not_found", []),
        ("name=hostDup and groups__name=groupA", ["hostDup"]),
        ("name=hostDup and groups__name=groupB", ["hostDup"]),
    ],
)
def test_basic_hybrid_search(host_filter_inventory, get, admin_user, host_filter, expected):
    response = host_filter_get(get, admin_user, host_filter)
    assert response.status_code == 200
    assert get_host_names(response) == sorted(expected)


@pytest.mark.django_db
def test_smart_search(get, admin_user):
    org = Organization.objects.create(name="search-org")
    inv = Inventory.objects.create(name="search-inv", organization=org)
    host = Host.objects.create(name="unique_search_target", description="findme_description", inventory=inv)

    for search_term in ["unique_search_target", "findme_description"]:
        response = host_filter_get(get, admin_user, "search=%s" % search_term)
        assert response.status_code == 200
        names = get_host_names(response)
        assert host.name in names


@pytest.mark.django_db
def test_password_field_filter_blocked(get, admin_user):
    url = reverse('api:host_list')
    filters = [
        "created_by__password__icontains=pas3w3rd",
        "search=foo or created_by__password__icontains=pas3w3rd",
        "created_by__password__icontains=passw3rd or search=foo",
    ]
    for f in filters:
        params = "?host_filter=%s" % urllib.parse.quote(f, safe='')
        response = get(url + params, admin_user)
        assert response.status_code == 400, f"Expected 400 for filter: {f}"


@pytest.mark.django_db
def test_unicode_host_filter(get, admin_user):
    org = Organization.objects.create(name="unicode-org")
    inv = Inventory.objects.create(name="unicode-inv", organization=org)
    host = Host.objects.create(name="ホスト", inventory=inv)
    group = Group.objects.create(name="グループ", inventory=inv)
    group.hosts.add(host)

    response = host_filter_get(get, admin_user, "name=ホスト")
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == host.id

    response = host_filter_get(get, admin_user, "groups__name=グループ")
    assert response.status_code == 200
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == host.id


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid_filter",
    ["string_without_equals", "1", "1.0", "true"],
    ids=["bare_string", "integer", "float", "bool"],
)
def test_invalid_host_filter(get, admin_user, invalid_filter):
    url = reverse('api:host_list')
    params = "?host_filter=%s" % urllib.parse.quote(invalid_filter, safe='')
    response = get(url + params, admin_user)
    assert response.status_code == 400


@pytest.fixture
def hosts_with_job_summaries():
    """Three hosts: one with a failed last job, one with a successful last job, one with no job."""
    org = Organization.objects.create(name='summary-org')
    inv = Inventory.objects.create(name='summary-inv', organization=org)
    host_failed = Host.objects.create(name='host-failed', inventory=inv)
    host_ok = Host.objects.create(name='host-ok', inventory=inv)
    Host.objects.create(name='host-no-job', inventory=inv)
    group = Group.objects.create(name='summary-group', inventory=inv)
    group.hosts.add(host_failed, host_ok)

    job = Job(inventory=inv)
    job.save()
    host_map = {h.name: h.id for h in inv.hosts.all()}
    JobEvent.create_from_data(
        job_id=job.pk,
        parent_uuid='abc123',
        event='playbook_on_stats',
        event_data={
            'ok': {host_ok.name: 1},
            'changed': {},
            'dark': {},
            'failures': {host_failed.name: 1},
            'ignored': {},
            'processed': {},
            'rescued': {},
            'skipped': {},
        },
        host_map=host_map,
    ).save()

    return {'inventory': inv, 'group': group}


@pytest.mark.django_db
def test_last_job_host_summary_failed_filter(hosts_with_job_summaries, get, admin_user):
    """?last_job_host_summary__failed=True returns only hosts whose latest job summary is failed."""
    url = reverse('api:host_list') + '?last_job_host_summary__failed=True'
    response = get(url, admin_user)
    assert response.status_code == 200
    names = get_host_names(response)
    assert names == ['host-failed']


@pytest.mark.django_db
def test_not_last_job_host_summary_failed_filter(hosts_with_job_summaries, get, admin_user):
    """?not__last_job_host_summary__failed=True returns only hosts whose latest job summary is not failed."""
    url = reverse('api:host_list') + '?not__last_job_host_summary__failed=True'
    response = get(url, admin_user)
    assert response.status_code == 200
    names = get_host_names(response)
    assert names == ['host-ok']


@pytest.mark.django_db
def test_inventory_last_job_host_summary_failed_filter(hosts_with_job_summaries, get, admin_user):
    inv = hosts_with_job_summaries['inventory']
    url = reverse('api:inventory_hosts_list', kwargs={'pk': inv.pk}) + '?last_job_host_summary__failed=True'
    response = get(url, admin_user)
    assert response.status_code == 200
    names = get_host_names(response)
    assert names == ['host-failed']


@pytest.mark.django_db
def test_inventory_not_last_job_host_summary_failed_filter(hosts_with_job_summaries, get, admin_user):
    inv = hosts_with_job_summaries['inventory']
    url = reverse('api:inventory_hosts_list', kwargs={'pk': inv.pk}) + '?not__last_job_host_summary__failed=True'
    response = get(url, admin_user)
    assert response.status_code == 200
    names = get_host_names(response)
    assert names == ['host-ok']


@pytest.mark.django_db
def test_group_all_hosts_last_job_host_summary_failed_filter(hosts_with_job_summaries, get, admin_user):
    group = hosts_with_job_summaries['group']
    url = reverse('api:group_all_hosts_list', kwargs={'pk': group.pk}) + '?last_job_host_summary__failed=True'
    response = get(url, admin_user)
    assert response.status_code == 200
    names = get_host_names(response)
    assert names == ['host-failed']


@pytest.mark.django_db
def test_group_all_hosts_not_last_job_host_summary_failed_filter(hosts_with_job_summaries, get, admin_user):
    group = hosts_with_job_summaries['group']
    url = reverse('api:group_all_hosts_list', kwargs={'pk': group.pk}) + '?not__last_job_host_summary__failed=True'
    response = get(url, admin_user)
    assert response.status_code == 200
    names = get_host_names(response)
    assert names == ['host-ok']
