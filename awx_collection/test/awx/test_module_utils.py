from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import sys

from awx.main.models import Organization, Team, Project, Inventory
from requests.models import Response
from unittest import mock


def getheader(self, header_name, default):
    mock_headers = {'X-API-Product-Name': 'not-junk', 'X-API-Product-Version': '1.2.3'}
    return mock_headers.get(header_name, default)


def read(self):
    return json.dumps({})


def status(self):
    return 200


def mock_ping_response(self, method, url, **kwargs):
    r = Response()
    r.getheader = getheader.__get__(r)
    r.read = read.__get__(r)
    r.status = status.__get__(r)
    return r


def test_version_warning(collection_import, silence_warning):
    TowerAPIModule = collection_import('plugins.module_utils.tower_api').TowerAPIModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_ping_response):
            my_module = TowerAPIModule(argument_spec=dict())
            my_module._COLLECTION_VERSION = "1.0.0"
            my_module._COLLECTION_TYPE = "not-junk"
            my_module.collection_to_version['not-junk'] = 'not-junk'
            my_module.get_endpoint('ping')
    silence_warning.assert_called_once_with(
        'You are running collection version 1.0.0 but connecting to tower version 1.2.3'
    )


def test_type_warning(collection_import, silence_warning):
    TowerAPIModule = collection_import('plugins.module_utils.tower_api').TowerAPIModule
    cli_data = {'ANSIBLE_MODULE_ARGS': {}}
    testargs = ['module_file2.py', json.dumps(cli_data)]
    with mock.patch.object(sys, 'argv', testargs):
        with mock.patch('ansible.module_utils.urls.Request.open', new=mock_ping_response):
            my_module = TowerAPIModule(argument_spec={})
            my_module._COLLECTION_VERSION = "1.2.3"
            my_module._COLLECTION_TYPE = "junk"
            my_module.collection_to_version['junk'] = 'junk'
            my_module.get_endpoint('ping')
    silence_warning.assert_called_once_with(
        'You are using the junk version of this collection but connecting to not-junk'
    )


def test_duplicate_config(collection_import, silence_warning):
    # imports done here because of PATH issues unique to this test suite
    TowerAPIModule = collection_import('plugins.module_utils.tower_api').TowerAPIModule
    data = {
        'name': 'zigzoom',
        'zig': 'zoom',
        'tower_username': 'bob',
        'tower_config_file': 'my_config'
    }

    with mock.patch.object(TowerAPIModule, 'load_config') as mock_load:
        argument_spec = dict(
            name=dict(required=True),
            zig=dict(type='str'),
        )
        TowerAPIModule(argument_spec=argument_spec, direct_params=data)
        assert mock_load.mock_calls[-1] == mock.call('my_config')

    silence_warning.assert_called_once_with(
        'The parameter(s) tower_username were provided at the same time as '
        'tower_config_file. Precedence may be unstable, '
        'we suggest either using config file or params.'
    )


def test_no_templated_values(collection_import):
    """This test corresponds to replacements done by
    awx_collection/tools/roles/template_galaxy/tasks/main.yml
    Those replacements should happen at build time, so they should not be
    checked into source.
    """
    TowerAPIModule = collection_import('plugins.module_utils.tower_api').TowerAPIModule
    assert TowerAPIModule._COLLECTION_VERSION == "0.0.1-devel", (
        'The collection version is templated when the collection is built '
        'and the code should retain the placeholder of "0.0.1-devel".'
    )
    InventoryModule = collection_import('plugins.inventory.tower').InventoryModule
    assert InventoryModule.NAME == 'awx.awx.tower', (
        'The inventory plugin FQCN is templated when the collection is built '
        'and the code should retain the default of awx.awx.'
    )


def test_conflicting_name_and_id(run_module, admin_user):
    """In the event that 2 related items match our search criteria in this way:
    one item has an id that matches input
    one item has a name that matches input
    We should preference the id over the name.
    Otherwise, the universality of the tower_api lookup plugin is compromised.
    """
    org_by_id = Organization.objects.create(name='foo')
    slug = str(org_by_id.id)
    org_by_name = Organization.objects.create(name=slug)
    result = run_module('tower_team', {
        'name': 'foo_team', 'description': 'fooin around',
        'organization': slug
    }, admin_user)
    assert not result.get('failed', False), result.get('msg', result)
    team = Team.objects.filter(name='foo_team').first()
    assert str(team.organization_id) == slug, (
        'Lookup by id should be preferenced over name in cases of conflict.'
    )
    assert team.organization.name == 'foo'


def test_multiple_lookup(run_module, admin_user):
    org1 = Organization.objects.create(name='foo')
    org2 = Organization.objects.create(name='bar')
    inv = Inventory.objects.create(name='Foo Inv')
    proj1 = Project.objects.create(name='foo', organization=org1, scm_type='git', scm_url="https://github.com/ansible/ansible-tower-samples",)
    proj2 = Project.objects.create(name='foo', organization=org2, scm_type='git', scm_url="https://github.com/ansible/ansible-tower-samples",)
    result = run_module('tower_job_template', {
        'name': 'Demo Job Template', 'project': proj1.name, 'inventory': inv.id, 'playbook': 'hello_world.yml'
    }, admin_user)
    assert result.get('failed', False)
    assert 'projects' in result['msg']
    assert 'foo' in result['msg']
    assert 'returned 2 items, expected 1' in result['msg']
    assert 'query' in result
