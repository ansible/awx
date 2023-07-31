from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import sys

from awx.main.models import Organization, Team, Project, Inventory
from requests.models import Response
from unittest import mock

awx_name = 'AWX'
controller_name = 'Red Hat Ansible Automation Platform'
ping_version = '1.2.3'


def getTowerheader(self, header_name, default):
    mock_headers = {'X-API-Product-Name': controller_name, 'X-API-Product-Version': ping_version}
    return mock_headers.get(header_name, default)


def getAWXheader(self, header_name, default):
    mock_headers = {'X-API-Product-Name': awx_name, 'X-API-Product-Version': ping_version}
    return mock_headers.get(header_name, default)


def getNoheader(self, header_name, default):
    mock_headers = {}
    return mock_headers.get(header_name, default)


def read(self):
    return json.dumps({})


def status(self):
    return 200


def mock_controller_ping_response(self, method, url, **kwargs):
    r = Response()
    r.getheader = getTowerheader.__get__(r)
    r.read = read.__get__(r)
    r.status = status.__get__(r)
    return r


def mock_awx_ping_response(self, method, url, **kwargs):
    r = Response()
    r.getheader = getAWXheader.__get__(r)
    r.read = read.__get__(r)
    r.status = status.__get__(r)
    return r


def mock_no_ping_response(self, method, url, **kwargs):
    r = Response()
    r.getheader = getNoheader.__get__(r)
    r.read = read.__get__(r)
    r.status = status.__get__(r)
    return r


def test_version_warning(collection_import, silence_warning):
    ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_awx_ping_response):
            my_module = ControllerAPIModule(argument_spec=dict())
            my_module._COLLECTION_VERSION = "2.0.0"
            my_module._COLLECTION_TYPE = "awx"
            my_module.get_endpoint('ping')
    silence_warning.assert_called_once_with(
        'You are running collection version {0} but connecting to {1} version {2}'.format(my_module._COLLECTION_VERSION, awx_name, ping_version)
    )


def test_version_warning_strictness_awx(collection_import, silence_warning):
    ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    # Compare 1.0.0 to 1.2.3 (major matches)
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_awx_ping_response):
            my_module = ControllerAPIModule(argument_spec=dict())
            my_module._COLLECTION_VERSION = "1.0.0"
            my_module._COLLECTION_TYPE = "awx"
            my_module.get_endpoint('ping')
    silence_warning.assert_not_called()

    # Compare 1.2.0 to 1.2.3 (major matches minor does not count)
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_awx_ping_response):
            my_module = ControllerAPIModule(argument_spec=dict())
            my_module._COLLECTION_VERSION = "1.2.0"
            my_module._COLLECTION_TYPE = "awx"
            my_module.get_endpoint('ping')
    silence_warning.assert_not_called()


def test_version_warning_strictness_controller(collection_import, silence_warning):
    ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    # Compare 1.2.0 to 1.2.3 (major/minor matches)
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_controller_ping_response):
            my_module = ControllerAPIModule(argument_spec=dict())
            my_module._COLLECTION_VERSION = "1.2.0"
            my_module._COLLECTION_TYPE = "controller"
            my_module.get_endpoint('ping')
    silence_warning.assert_not_called()

    # Compare 1.0.0 to 1.2.3 (major/minor fail to match)
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_controller_ping_response):
            my_module = ControllerAPIModule(argument_spec=dict())
            my_module._COLLECTION_VERSION = "1.0.0"
            my_module._COLLECTION_TYPE = "controller"
            my_module.get_endpoint('ping')
    silence_warning.assert_called_once_with(
        'You are running collection version {0} but connecting to {1} version {2}'.format(my_module._COLLECTION_VERSION, controller_name, ping_version)
    )


def test_type_warning(collection_import, silence_warning):
    ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_awx_ping_response):
            my_module = ControllerAPIModule(argument_spec={})
            my_module._COLLECTION_VERSION = ping_version
            my_module._COLLECTION_TYPE = "controller"
            my_module.get_endpoint('ping')
    silence_warning.assert_called_once_with(
        'You are using the {0} version of this collection but connecting to {1}'.format(my_module._COLLECTION_TYPE, awx_name)
    )


def test_duplicate_config(collection_import, silence_warning):
    # imports done here because of PATH issues unique to this test suite
    ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    data = {'name': 'zigzoom', 'zig': 'zoom', 'controller_username': 'bob', 'controller_config_file': 'my_config'}

    with mock.patch.object(ControllerAPIModule, 'load_config') as mock_load:
        argument_spec = dict(
            name=dict(required=True),
            zig=dict(type='str'),
        )
        ControllerAPIModule(argument_spec=argument_spec, direct_params=data)
        assert mock_load.mock_calls[-1] == mock.call('my_config')

    silence_warning.assert_called_once_with(
        'The parameter(s) controller_username were provided at the same time as '
        'controller_config_file. Precedence may be unstable, '
        'we suggest either using config file or params.'
    )


def test_no_templated_values(collection_import):
    """This test corresponds to replacements done by
    awx_collection/tools/roles/template_galaxy/tasks/main.yml
    Those replacements should happen at build time, so they should not be
    checked into source.
    """
    ControllerAPIModule = collection_import('plugins.module_utils.controller_api').ControllerAPIModule
    assert ControllerAPIModule._COLLECTION_VERSION == "0.0.1-devel", (
        'The collection version is templated when the collection is built ' 'and the code should retain the placeholder of "0.0.1-devel".'
    )
    InventoryModule = collection_import('plugins.inventory.controller').InventoryModule
    assert InventoryModule.NAME == 'awx.awx.controller', (
        'The inventory plugin FQCN is templated when the collection is built ' 'and the code should retain the default of awx.awx.'
    )


def test_conflicting_name_and_id(run_module, admin_user):
    """In the event that 2 related items match our search criteria in this way:
    one item has an id that matches input
    one item has a name that matches input
    We should preference the id over the name.
    Otherwise, the universality of the controller_api lookup plugin is compromised.
    """
    org_by_id = Organization.objects.create(name='foo')
    slug = str(org_by_id.id)
    Organization.objects.create(name=slug)
    result = run_module('team', {'name': 'foo_team', 'description': 'fooin around', 'organization': slug}, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    team = Team.objects.filter(name='foo_team').first()
    assert str(team.organization_id) == slug, 'Lookup by id should be preferenced over name in cases of conflict.'
    assert team.organization.name == 'foo'


def test_multiple_lookup(run_module, admin_user):
    org1 = Organization.objects.create(name='foo')
    org2 = Organization.objects.create(name='bar')
    inv = Inventory.objects.create(name='Foo Inv')
    proj1 = Project.objects.create(
        name='foo',
        organization=org1,
        scm_type='git',
        scm_url="https://github.com/ansible/ansible-tower-samples",
    )
    Project.objects.create(
        name='foo',
        organization=org2,
        scm_type='git',
        scm_url="https://github.com/ansible/ansible-tower-samples",
    )
    result = run_module('job_template', {'name': 'Demo Job Template', 'project': proj1.name, 'inventory': inv.id, 'playbook': 'hello_world.yml'}, admin_user)
    assert result.get('failed', False)
    assert 'projects' in result['msg']
    assert 'foo' in result['msg']
    assert 'returned 2 items, expected 1' in result['msg']
    assert 'query' in result
