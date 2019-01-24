# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import re
import logging
from collections import OrderedDict


# Logger is used for any data-related messages so that the log level
# can be adjusted on command invocation
logger = logging.getLogger('awx.main.commands.inventory_import')


__all__ = ['MemHost', 'MemGroup', 'MemInventory',
           'mem_data_to_dict', 'dict_to_mem_data']


ipv6_port_re = re.compile(r'^\[([A-Fa-f0-9:]{3,})\]:(\d+?)$')


# Models for in-memory objects that represent an inventory


class MemObject(object):
    '''
    Common code shared between in-memory groups and hosts.
    '''

    def __init__(self, name):
        assert name, 'no name'
        self.name = name


class MemGroup(MemObject):
    '''
    In-memory representation of an inventory group.
    '''

    def __init__(self, name):
        super(MemGroup, self).__init__(name)
        self.children = []
        self.hosts = []
        self.variables = {}
        self.parents = []
        # Used on the "all" group in place of previous global variables.
        # maps host and group names to hosts to prevent redudant additions
        self.all_hosts = {}
        self.all_groups = {}
        self.variables = {}
        logger.debug('Loaded group: %s', self.name)

    def __repr__(self):
        return '<_in-memory-group_ `{}`>'.format(self.name)

    def add_child_group(self, group):
        assert group.name != 'all', 'group name is all'
        assert isinstance(group, MemGroup), 'not MemGroup instance'
        logger.debug('Adding child group %s to parent %s', group.name, self.name)
        if group not in self.children:
            self.children.append(group)
        if self not in group.parents:
            group.parents.append(self)

    def add_host(self, host):
        assert isinstance(host, MemHost), 'not MemHost instance'
        logger.debug('Adding host %s to group %s', host.name, self.name)
        if host not in self.hosts:
            self.hosts.append(host)

    def debug_tree(self, group_names=None):
        group_names = group_names or set()
        if self.name in group_names:
            return
        logger.debug('Dumping tree for group "%s":', self.name)
        logger.debug('- Vars: %r', self.variables)
        for h in self.hosts:
            logger.debug('- Host: %s, %r',  h.name, h.variables)
        for g in self.children:
            logger.debug('- Child: %s', g.name)
        logger.debug('----')
        group_names.add(self.name)
        for g in self.children:
            g.debug_tree(group_names)


class MemHost(MemObject):
    '''
    In-memory representation of an inventory host.
    '''

    def __init__(self, name, port=None):
        super(MemHost, self).__init__(name)
        self.variables = {}
        self.instance_id = None
        self.name = name
        if port:
            # was `ansible_ssh_port` in older Ansible versions
            self.variables['ansible_port'] = port
        logger.debug('Loaded host: %s', self.name)

    def __repr__(self):
        return '<_in-memory-host_ `{}`>'.format(self.name)


class MemInventory(object):
    '''
    Common functions for an inventory loader from a given source.
    '''
    def __init__(self, all_group=None, group_filter_re=None, host_filter_re=None):
        if all_group:
            assert isinstance(all_group, MemGroup), '{} is not MemGroup instance'.format(all_group)
            self.all_group = all_group
        else:
            self.all_group = self.create_group('all')
        self.group_filter_re = group_filter_re
        self.host_filter_re = host_filter_re

    def create_host(self, host_name, port):
        host = MemHost(host_name, port)
        self.all_group.all_hosts[host_name] = host
        return host

    def get_host(self, name):
        '''
        Return a MemHost instance from host name, creating if needed.  If name
        contains brackets, they will NOT be interpreted as a host pattern.
        '''
        m = ipv6_port_re.match(name)
        if m:
            host_name = m.groups()[0]
            port = int(m.groups()[1])
        elif name.count(':') == 1:
            host_name = name.split(':')[0]
            try:
                port = int(name.split(':')[1])
            except (ValueError, UnicodeDecodeError):
                logger.warning(u'Invalid port "%s" for host "%s"',
                               name.split(':')[1], host_name)
                port = None
        else:
            host_name = name
            port = None
        if self.host_filter_re and not self.host_filter_re.match(host_name):
            logger.debug('Filtering host %s', host_name)
            return None
        if host_name not in self.all_group.all_hosts:
            self.create_host(host_name, port)
        return self.all_group.all_hosts[host_name]

    def create_group(self, group_name):
        group = MemGroup(group_name)
        if group_name not in ['all', 'ungrouped']:
            self.all_group.all_groups[group_name] = group
        return group

    def get_group(self, name, all_group=None, child=False):
        '''
        Return a MemGroup instance from group name, creating if needed.
        '''
        all_group = all_group or self.all_group
        if name in ['all', 'ungrouped']:
            return all_group
        if self.group_filter_re and not self.group_filter_re.match(name):
            logger.debug('Filtering group %s', name)
            return None
        if name not in self.all_group.all_groups:
            group = self.create_group(name)
            if not child:
                all_group.add_child_group(group)
        return self.all_group.all_groups[name]

    def delete_empty_groups(self):
        for name, group in list(self.all_group.all_groups.items()):
            if not group.children and not group.hosts and not group.variables:
                logger.debug('Removing empty group %s', name)
                for parent in group.parents:
                    if group in parent.children:
                        parent.children.remove(group)
                del self.all_group.all_groups[name]


# Conversion utilities

def mem_data_to_dict(inventory):
    '''
    Given an in-memory construct of an inventory, returns a dictionary that
    follows Ansible guidelines on the structure of dynamic inventory sources

    May be replaced by removing in-memory constructs within this file later
    '''
    all_group = inventory.all_group
    inventory_data = OrderedDict([])
    # Save hostvars to _meta
    inventory_data['_meta'] = OrderedDict([])
    hostvars = OrderedDict([])
    for name, host_obj in all_group.all_hosts.items():
        hostvars[name] = host_obj.variables
    inventory_data['_meta']['hostvars'] = hostvars
    # Save children of `all` group
    inventory_data['all'] = OrderedDict([])
    if all_group.variables:
        inventory_data['all']['vars'] = all_group.variables
    inventory_data['all']['children'] = [c.name for c in all_group.children]
    inventory_data['all']['children'].append('ungrouped')
    # Save details of declared groups individually
    ungrouped_hosts = set(all_group.all_hosts.keys())
    for name, group_obj in all_group.all_groups.items():
        group_host_names = [h.name for h in group_obj.hosts]
        group_children_names = [c.name for c in group_obj.children]
        group_data = OrderedDict([])
        if group_host_names:
            group_data['hosts'] = group_host_names
            ungrouped_hosts.difference_update(group_host_names)
        if group_children_names:
            group_data['children'] = group_children_names
        if group_obj.variables:
            group_data['vars'] = group_obj.variables
        inventory_data[name] = group_data
    # Save ungrouped hosts
    inventory_data['ungrouped'] = OrderedDict([])
    if ungrouped_hosts:
        inventory_data['ungrouped']['hosts'] = list(ungrouped_hosts)
    return inventory_data


def dict_to_mem_data(data, inventory=None):
    '''
    In-place operation on `inventory`, adds contents from `data` to the
    in-memory representation of memory.
    May be destructive on `data`
    '''
    assert isinstance(data, dict), 'Expected dict, received {}'.format(type(data))
    if inventory is None:
        inventory = MemInventory()

    _meta = data.pop('_meta', {})

    for k,v in data.items():
        group = inventory.get_group(k)
        if not group:
            continue

        # Load group hosts/vars/children from a dictionary.
        if isinstance(v, dict):
            # Process hosts within a group.
            hosts = v.get('hosts', {})
            if isinstance(hosts, dict):
                for hk, hv in hosts.items():
                    host = inventory.get_host(hk)
                    if not host:
                        continue
                    if isinstance(hv, dict):
                        host.variables.update(hv)
                    else:
                        logger.warning('Expected dict of vars for '
                                       'host "%s", got %s instead',
                                       hk, str(type(hv)))
                    group.add_host(host)
            elif isinstance(hosts, (list, tuple)):
                for hk in hosts:
                    host = inventory.get_host(hk)
                    if not host:
                        continue
                    group.add_host(host)
            else:
                logger.warning('Expected dict or list of "hosts" for '
                               'group "%s", got %s instead', k,
                               str(type(hosts)))
            # Process group variables.
            vars = v.get('vars', {})
            if isinstance(vars, dict):
                group.variables.update(vars)
            else:
                logger.warning('Expected dict of vars for '
                               'group "%s", got %s instead',
                               k, str(type(vars)))
            # Process child groups.
            children = v.get('children', [])
            if isinstance(children, (list, tuple)):
                for c in children:
                    child = inventory.get_group(c, inventory.all_group, child=True)
                    if child and c != 'ungrouped':
                        group.add_child_group(child)
            else:
                logger.warning('Expected list of children for '
                               'group "%s", got %s instead',
                               k, str(type(children)))

        # Load host names from a list.
        elif isinstance(v, (list, tuple)):
            for h in v:
                host = inventory.get_host(h)
                if not host:
                    continue
                group.add_host(host)
        else:
            logger.warning('')
            logger.warning('Expected dict or list for group "%s", '
                           'got %s instead', k, str(type(v)))

        if k not in ['all', 'ungrouped']:
            inventory.all_group.add_child_group(group)

    if _meta:
        for k,v in inventory.all_group.all_hosts.items():
            meta_hostvars = _meta['hostvars'].get(k, {})
            if isinstance(meta_hostvars, dict):
                v.variables.update(meta_hostvars)
            else:
                logger.warning('Expected dict of vars for '
                               'host "%s", got %s instead',
                               k, str(type(meta_hostvars)))

    return inventory
