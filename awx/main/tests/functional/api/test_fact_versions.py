# Python
from unittest import mock
import pytest
from datetime import timedelta
import urllib.parse

# AWX
from awx.api.versioning import reverse
from awx.main.models.fact import Fact
from awx.main.utils import timestamp_apiformat

# Django
from django.utils import timezone


def mock_feature_enabled(feature):
    return True


def mock_feature_disabled(feature):
    return False


def setup_common(hosts, fact_scans, get, user, epoch=timezone.now(), get_params={}, host_count=1):
    hosts = hosts(host_count=host_count)
    fact_scans(fact_scans=3, timestamp_epoch=epoch)

    url = reverse('api:host_fact_versions_list', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True), data=get_params)

    return (hosts[0], response)


def check_url(url1_full, fact_known, module):
    url1_split = urllib.parse.urlsplit(url1_full)
    url1 = url1_split.path
    url1_params = urllib.parse.parse_qsl(url1_split.query)

    url2 = reverse('api:host_fact_compare_view', kwargs={'pk': fact_known.host.pk})
    url2_params = [('module', module), ('datetime', timestamp_apiformat(fact_known.timestamp))]

    assert url1 == url2
    # Sort before comparing because urlencode can't be trusted
    url1_params_sorted = sorted(url1_params, key=lambda val: val[0])
    url2_params_sorted = sorted(url2_params, key=lambda val: val[0])
    assert urllib.parse.urlencode(url1_params_sorted) == urllib.parse.urlencode(url2_params_sorted)


def check_response_facts(facts_known, response):
    for i, fact_known in enumerate(facts_known):
        assert fact_known.module == response.data['results'][i]['module']
        assert timestamp_apiformat(fact_known.timestamp) == response.data['results'][i]['timestamp']
        check_url(response.data['results'][i]['related']['fact_view'], fact_known, fact_known.module)


def check_system_tracking_feature_forbidden(response):
    assert 402 == response.status_code
    assert 'Your license does not permit use of system tracking.' == response.data['detail']


@mock.patch('awx.api.views.mixin.feature_enabled', new=mock_feature_disabled)
@pytest.mark.django_db
@pytest.mark.license_feature
def test_system_tracking_license_get(hosts, get, user):
    hosts = hosts(host_count=1)
    url = reverse('api:host_fact_versions_list', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True))

    check_system_tracking_feature_forbidden(response)


@mock.patch('awx.api.views.mixin.feature_enabled', new=mock_feature_disabled)
@pytest.mark.django_db
@pytest.mark.license_feature
def test_system_tracking_license_options(hosts, options, user):
    hosts = hosts(host_count=1)
    url = reverse('api:host_fact_versions_list', kwargs={'pk': hosts[0].pk})
    response = options(url, None, user('admin', True))

    check_system_tracking_feature_forbidden(response)


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
@pytest.mark.license_feature
def test_no_facts_db(hosts, get, user):
    hosts = hosts(host_count=1)
    url = reverse('api:host_fact_versions_list', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True))

    response_expected = {
        'results': []
    }
    assert response_expected == response.data


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_basic_fields(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    search = {
        'from': epoch,
        'to': epoch,
    }

    (host, response) = setup_common(hosts, fact_scans, get, user, epoch=epoch, get_params=search)

    results = response.data['results']
    assert 'related' in results[0]
    assert 'timestamp' in results[0]
    assert 'module' in results[0]


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
@pytest.mark.license_feature
def test_basic_options_fields(hosts, fact_scans, options, user, monkeypatch_jsonbfield_get_db_prep_save):
    hosts = hosts(host_count=1)
    fact_scans(fact_scans=1)

    url = reverse('api:host_fact_versions_list', kwargs={'pk': hosts[0].pk})
    response = options(url, None, user('admin', True), pk=hosts[0].id)

    assert 'related' in response.data['actions']['GET']
    assert 'module' in response.data['actions']['GET']
    assert ("ansible", "Ansible") in response.data['actions']['GET']['module']['choices']
    assert ("services", "Services") in response.data['actions']['GET']['module']['choices']
    assert ("packages", "Packages") in response.data['actions']['GET']['module']['choices']


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_related_fact_view(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()

    (host, response) = setup_common(hosts, fact_scans, get, user, epoch=epoch)
    facts_known = Fact.get_timeline(host.id)
    assert 9 == len(facts_known)
    assert 9 == len(response.data['results'])

    for i, fact_known in enumerate(facts_known):
        check_url(response.data['results'][i]['related']['fact_view'], fact_known, fact_known.module)


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_multiple_hosts(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()

    (host, response) = setup_common(hosts, fact_scans, get, user, epoch=epoch, host_count=3)
    facts_known = Fact.get_timeline(host.id)
    assert 9 == len(facts_known)
    assert 9 == len(response.data['results'])

    for i, fact_known in enumerate(facts_known):
        check_url(response.data['results'][i]['related']['fact_view'], fact_known, fact_known.module)


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_param_to_from(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    search = {
        'from': epoch - timedelta(days=10),
        'to': epoch + timedelta(days=10),
    }

    (host, response) = setup_common(hosts, fact_scans, get, user, epoch=epoch, get_params=search)
    facts_known = Fact.get_timeline(host.id, ts_from=search['from'], ts_to=search['to'])
    assert 9 == len(facts_known)
    assert 9 == len(response.data['results'])

    check_response_facts(facts_known, response)


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_param_module(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    search = {
        'module': 'packages',
    }

    (host, response) = setup_common(hosts, fact_scans, get, user, epoch=epoch, get_params=search)
    facts_known = Fact.get_timeline(host.id, module=search['module'])
    assert 3 == len(facts_known)
    assert 3 == len(response.data['results'])

    check_response_facts(facts_known, response)


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_param_from(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    search = {
        'from': epoch + timedelta(days=1),
    }

    (host, response) = setup_common(hosts, fact_scans, get, user, epoch=epoch, get_params=search)
    facts_known = Fact.get_timeline(host.id, ts_from=search['from'])
    assert 3 == len(facts_known)
    assert 3 == len(response.data['results'])

    check_response_facts(facts_known, response)


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_param_to(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    search = {
        'to': epoch + timedelta(days=1),
    }

    (host, response) = setup_common(hosts, fact_scans, get, user, epoch=epoch, get_params=search)
    facts_known = Fact.get_timeline(host.id, ts_to=search['to'])
    assert 6 == len(facts_known)
    assert 6 == len(response.data['results'])

    check_response_facts(facts_known, response)


def _test_user_access_control(hosts, fact_scans, get, user_obj, team_obj):
    hosts = hosts(host_count=1)
    fact_scans(fact_scans=1)

    team_obj.member_role.members.add(user_obj)

    url = reverse('api:host_fact_versions_list', kwargs={'pk': hosts[0].pk})
    response = get(url, user_obj)
    return response


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.ac
@pytest.mark.django_db
def test_normal_user_403(hosts, fact_scans, get, user, team, monkeypatch_jsonbfield_get_db_prep_save):
    user_bob = user('bob', False)
    response = _test_user_access_control(hosts, fact_scans, get, user_bob, team)

    assert 403 == response.status_code
    assert "You do not have permission to perform this action."  == response.data['detail']


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.ac
@pytest.mark.django_db
def test_super_user_ok(hosts, fact_scans, get, user, team, monkeypatch_jsonbfield_get_db_prep_save):
    user_super = user('bob', True)
    response = _test_user_access_control(hosts, fact_scans, get, user_super, team)

    assert 200 == response.status_code


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.ac
@pytest.mark.django_db
def test_user_admin_ok(organization, hosts, fact_scans, get, user, team):
    user_admin = user('johnson', False)
    organization.admin_role.members.add(user_admin)

    response = _test_user_access_control(hosts, fact_scans, get, user_admin, team)

    assert 200 == response.status_code


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.ac
@pytest.mark.django_db
def test_user_admin_403(organization, organizations, hosts, fact_scans, get, user, team, monkeypatch_jsonbfield_get_db_prep_save):
    user_admin = user('johnson', False)
    org2 = organizations(1)
    org2[0].admin_role.members.add(user_admin)

    response = _test_user_access_control(hosts, fact_scans, get, user_admin, team)

    assert 403 == response.status_code
