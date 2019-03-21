from unittest import mock
import pytest
import json


from awx.api.versioning import reverse
from awx.main.utils import timestamp_apiformat
from django.utils import timezone


def mock_feature_enabled(feature):
    return True


def mock_feature_disabled(feature):
    return False


# TODO: Consider making the fact_scan() fixture a Class, instead of a function, and move this method into it
def find_fact(facts, host_id, module_name, timestamp):
    for f in facts:
        if f.host_id == host_id and f.module == module_name and f.timestamp == timestamp:
            return f
    raise RuntimeError('fact <%s, %s, %s> not found in %s', (host_id, module_name, timestamp, facts))


def setup_common(hosts, fact_scans, get, user, epoch=timezone.now(), module_name='ansible', get_params={}):
    hosts = hosts(host_count=1)
    facts = fact_scans(fact_scans=1, timestamp_epoch=epoch)

    url = reverse('api:host_fact_compare_view', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True), data=get_params)

    fact_known = find_fact(facts, hosts[0].id, module_name, epoch)
    return (fact_known, response)


def check_system_tracking_feature_forbidden(response):
    assert 402 == response.status_code
    assert 'Your license does not permit use of system tracking.' == response.data['detail']


@mock.patch('awx.api.views.mixin.feature_enabled', new=mock_feature_disabled)
@pytest.mark.django_db
@pytest.mark.license_feature
def test_system_tracking_license_get(hosts, get, user):
    hosts = hosts(host_count=1)
    url = reverse('api:host_fact_compare_view', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True))

    check_system_tracking_feature_forbidden(response)


@mock.patch('awx.api.views.mixin.feature_enabled', new=mock_feature_disabled)
@pytest.mark.django_db
@pytest.mark.license_feature
def test_system_tracking_license_options(hosts, options, user):
    hosts = hosts(host_count=1)
    url = reverse('api:host_fact_compare_view', kwargs={'pk': hosts[0].pk})
    response = options(url, None, user('admin', True))

    check_system_tracking_feature_forbidden(response)


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_no_fact_found(hosts, get, user):
    hosts = hosts(host_count=1)
    url = reverse('api:host_fact_compare_view', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True))

    expected_response = {
        "detail": "Fact not found."
    }
    assert 404 == response.status_code
    assert expected_response == response.data


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_basic_fields(hosts, fact_scans, get, user, monkeypatch_jsonbfield_get_db_prep_save):
    hosts = hosts(host_count=1)
    fact_scans(fact_scans=1)

    url = reverse('api:host_fact_compare_view', kwargs={'pk': hosts[0].pk})
    response = get(url, user('admin', True))

    assert 'related' in response.data
    assert 'id' in response.data
    assert 'facts' in response.data
    assert 'module' in response.data
    assert 'host' in response.data
    assert isinstance(response.data['host'], int)
    assert 'summary_fields' in response.data
    assert 'host' in response.data['summary_fields']
    assert 'name' in response.data['summary_fields']['host']
    assert 'description' in response.data['summary_fields']['host']
    assert 'host' in response.data['related']
    assert reverse('api:host_detail', kwargs={'pk': hosts[0].pk}) == response.data['related']['host']


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_content(hosts, fact_scans, get, user, fact_ansible_json, monkeypatch_jsonbfield_get_db_prep_save):
    (fact_known, response) = setup_common(hosts, fact_scans, get, user)

    assert fact_known.host_id == response.data['host']
    # TODO: Just make response.data['facts'] when we're only dealing with postgres, or if jsonfields ever fixes this bug
    assert fact_ansible_json == (json.loads(response.data['facts']) if isinstance(response.data['facts'], str) else response.data['facts'])
    assert timestamp_apiformat(fact_known.timestamp) == response.data['timestamp']
    assert fact_known.module == response.data['module']


def _test_search_by_module(hosts, fact_scans, get, user, fact_json, module_name):
    params = {
        'module': module_name
    }
    (fact_known, response) = setup_common(hosts, fact_scans, get, user, module_name=module_name, get_params=params)

    # TODO: Just make response.data['facts'] when we're only dealing with postgres, or if jsonfields ever fixes this bug
    assert fact_json == (json.loads(response.data['facts']) if isinstance(response.data['facts'], str) else response.data['facts'])
    assert timestamp_apiformat(fact_known.timestamp) == response.data['timestamp']
    assert module_name == response.data['module']


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_search_by_module_packages(hosts, fact_scans, get, user, fact_packages_json, monkeypatch_jsonbfield_get_db_prep_save):
    _test_search_by_module(hosts, fact_scans, get, user, fact_packages_json, 'packages')


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_search_by_module_services(hosts, fact_scans, get, user, fact_services_json, monkeypatch_jsonbfield_get_db_prep_save):
    _test_search_by_module(hosts, fact_scans, get, user, fact_services_json, 'services')


@mock.patch('awx.api.views.feature_enabled', new=mock_feature_enabled)
@pytest.mark.django_db
def test_search_by_timestamp_and_module(hosts, fact_scans, get, user, fact_packages_json, monkeypatch_jsonbfield_get_db_prep_save):
    epoch = timezone.now()
    module_name = 'packages'

    (fact_known, response) = setup_common(
        hosts, fact_scans, get, user, module_name=module_name, epoch=epoch,
        get_params=dict(module=module_name, datetime=epoch)
    )

    assert fact_known.id == response.data['id']


def _test_user_access_control(hosts, fact_scans, get, user_obj, team_obj):
    hosts = hosts(host_count=1)
    fact_scans(fact_scans=1)

    team_obj.member_role.members.add(user_obj)

    url = reverse('api:host_fact_compare_view', kwargs={'pk': hosts[0].pk})
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
def test_user_admin_ok(organization, hosts, fact_scans, get, user, team, monkeypatch_jsonbfield_get_db_prep_save):
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
