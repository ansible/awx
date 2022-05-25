#!/usr/bin/python

from tokenize import group
from .export_tools import parse_extra_vars_to_json
from .awx_request import get_awx_resource_by_id, get_awx_resources

def get_inventory_hosts(inventory, awx_auth):
    hosts = get_awx_resources('/api/v2/hosts/?inventory='+str(inventory['id']), previousPageResults=[], awx_auth=awx_auth)
    for host_index, host_item in enumerate(hosts):
        hosts[host_index]['variables'] = parse_extra_vars_to_json(host_item['variables'])
    return hosts

def get_hosts_by_group_id(group_id, awx_auth):
    hosts = get_awx_resources('/api/v2/hosts/?group='+str(group_id), previousPageResults=[], awx_auth=awx_auth)
    hosts_in_group = []
    for host in hosts:
        host_in_group = dict(
            name = host['name']
        )
        hosts_in_group.append(host_in_group)
    return hosts_in_group

def get_inventory_groups(inventory, awx_auth):
    groups = get_awx_resources('/api/v2/groups/?inventory='+str(inventory['id']), previousPageResults=[], awx_auth=awx_auth)
    for group_index, group_item in enumerate(groups):
        groups[group_index]['hosts'] = get_hosts_by_group_id(group_item['id'], awx_auth)
        groups[group_index]['variables'] = parse_extra_vars_to_json(group_item['variables'])
    return groups

def get_inventory_by_id(inventory_id, awx_auth):
    inventory = get_awx_resource_by_id('inventory', inventory_id, awx_auth)
    if inventory['has_inventory_sources']:
        inventory['inventory_sources'] = get_awx_resources('/api/v2/inventory_sources/?inventory='+str(inventory['id']), previousPageResults=[], awx_auth=awx_auth)
        for inventory_source_index, inventory_source in enumerate(inventory['inventory_sources']):
            inventory['inventory_sources'][inventory_source_index]['source_vars'] = parse_extra_vars_to_json(inventory_source['source_vars'])
        inventory['hosts'] = []
        inventory['groups'] = []
    else:
        inventory['inventory_sources'] = []
        inventory['hosts'] = get_inventory_hosts(inventory, awx_auth)
        inventory['groups'] = get_inventory_groups(inventory, awx_auth)
    inventory['variables'] = parse_extra_vars_to_json(inventory['variables'])
    return inventory

