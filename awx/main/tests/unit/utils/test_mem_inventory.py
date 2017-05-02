# AWX utils
from awx.main.utils.mem_inventory import (
    MemInventory,
    mem_data_to_dict, dict_to_mem_data
)

import pytest
import json


@pytest.fixture
def memory_inventory():
    inventory = MemInventory()
    h = inventory.get_host('my_host')
    h.variables = {'foo': 'bar'}
    g = inventory.get_group('my_group')
    g.variables = {'foobar': 'barfoo'}
    h2 = inventory.get_host('group_host')
    g.add_host(h2)
    return inventory


@pytest.fixture
def JSON_of_inv():
    # Implemented as fixture becuase it may be change inside of tests
    return {
        "_meta": {
            "hostvars": {
                "group_host": {},
                "my_host": {"foo": "bar"}
            }
        }, 
        "all": {"children": ["my_group",  "ungrouped"]},
        "my_group": {
            "hosts": ["group_host"],
            "vars": {"foobar": "barfoo"}
        },
        "ungrouped": {"hosts": ["my_host"]}
    }


# Structure mentioned in official docs
# https://docs.ansible.com/ansible/dev_guide/developing_inventory.html
@pytest.fixture
def JSON_with_lists():
    docs_example = '''{
       "databases"   : {
           "hosts"   : [ "host1.example.com", "host2.example.com" ],
           "vars"    : {
               "a"   : true
           }
       },
       "webservers"  : [ "host2.example.com", "host3.example.com" ],
       "atlanta"     : {
           "hosts"   : [ "host1.example.com", "host4.example.com", "host5.example.com" ],
           "vars"    : {
               "b"   : false
           },
           "children": [ "marietta", "5points" ]
       },
       "marietta"    : [ "host6.example.com" ],
       "5points"     : [ "host7.example.com" ]
    }'''
    return json.loads(docs_example)


# MemObject basic operations tests

@pytest.mark.inventory_import
def test_inventory_create_all_group():
    inventory = MemInventory()
    assert inventory.all_group.name == 'all'


@pytest.mark.inventory_import
def test_create_child_group():
    inventory = MemInventory()
    g1 = inventory.get_group('g1')
    # Create new group by name as child of g1
    g2 = inventory.get_group('g2', g1)
    # Check that child is in the children of the parent group
    assert g1.children == [g2]
    # Check that _only_ the parent group is listed as a root group
    assert inventory.all_group.children == [g1]
    # Check that _both_ are tracked by the global `all_groups` dict
    assert set(inventory.all_group.all_groups.values()) == set([g1, g2])


@pytest.mark.inventory_import
def test_ungrouped_mechanics():
    # ansible-inventory returns a group called `ungrouped`
    # we can safely treat this the same as the `all_group`
    inventory = MemInventory()
    ug = inventory.get_group('ungrouped')
    assert ug is inventory.all_group


# MemObject --> JSON tests

@pytest.mark.inventory_import
def test_convert_memory_to_JSON_with_vars(memory_inventory):
    data = mem_data_to_dict(memory_inventory)
    # Assertions about the variables on the objects
    assert data['_meta']['hostvars']['my_host'] == {'foo': 'bar'}
    assert data['my_group']['vars'] == {'foobar': 'barfoo'}
    # Orphan host should be found in ungrouped false group
    assert data['ungrouped']['hosts'] == ['my_host']


# JSON --> MemObject tests

@pytest.mark.inventory_import
def test_convert_JSON_to_memory_with_vars(JSON_of_inv):
    inventory = dict_to_mem_data(JSON_of_inv)
    # Assertions about the variables on the objects
    assert inventory.get_host('my_host').variables == {'foo': 'bar'}
    assert inventory.get_group('my_group').variables == {'foobar': 'barfoo'}
    # Host should be child of group
    assert inventory.get_host('group_host') in inventory.get_group('my_group').hosts


@pytest.mark.inventory_import
def test_host_lists_accepted(JSON_with_lists):
    inventory = dict_to_mem_data(JSON_with_lists)
    assert inventory.get_group('marietta').name == 'marietta'
    # Check that marietta's hosts was saved
    h = inventory.get_host('host6.example.com')
    assert h.name == 'host6.example.com'
