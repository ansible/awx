#!/usr/bin/env python

# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import glob
import json
import logging
import os
import shlex
import argparse
import re
import string
import yaml

# import sys
# # Add awx/plugins to sys.path so we can use the plugin
# TEST_DIR = os.path.dirname(__file__)
# path = os.path.abspath(os.path.join(TEST_DIR, '..', '..', 'main', 'utils'))
# if path not in sys.path:
#     sys.path.insert(0, path)

# AWX
from awx.main.utils.mem_inventory import (
    MemGroup, MemInventory, mem_data_to_dict, ipv6_port_re
)  # NOQA


# Logger is used for any data-related messages so that the log level
# can be adjusted on command invocation
# logger = logging.getLogger('awx.plugins.ansible_inventory.tower_inventory_legacy')
logger = logging.getLogger('awx.main.management.commands.inventory_import')


class FileMemInventory(MemInventory):
    '''
    Adds on file-specific actions
    '''
    def __init__(self, source_dir, all_group, group_filter_re, host_filter_re, **kwargs):
        super(FileMemInventory, self).__init__(all_group, group_filter_re, host_filter_re, **kwargs)
        self.source_dir = source_dir

    def load_vars(self, mem_object, dir_path):
        all_vars = {}
        files_found = 0
        for suffix in ('', '.yml', '.yaml', '.json'):
            path = ''.join([dir_path, suffix]).encode("utf-8")
            if not os.path.exists(path):
                continue
            if not os.path.isfile(path):
                continue
            files_found += 1
            if files_found > 1:
                raise RuntimeError(
                    'Multiple variable files found. There should only '
                    'be one. %s ' % self.name)
            vars_name = os.path.basename(os.path.dirname(path))
            logger.debug('Loading %s from %s', vars_name, path)
            try:
                v = yaml.safe_load(file(path, 'r').read())
                if hasattr(v, 'items'): # is a dict
                    all_vars.update(v)
            except yaml.YAMLError as e:
                if hasattr(e, 'problem_mark'):
                    logger.error('Invalid YAML in %s:%s col %s', path,
                                 e.problem_mark.line + 1,
                                 e.problem_mark.column + 1)
                else:
                    logger.error('Error loading YAML from %s', path)
                raise
        return all_vars

    def create_host(self, host_name, port):
        host = super(FileMemInventory, self).create_host(host_name, port)
        host_vars_dir = os.path.join(self.source_dir, 'host_vars', host.name)
        host.variables.update(self.load_vars(host, host_vars_dir))
        return host

    def create_group(self, group_name):
        group = super(FileMemInventory, self).create_group(group_name)
        group_vars_dir = os.path.join(self.source_dir, 'group_vars', group.name)
        group.variables.update(self.load_vars(group, group_vars_dir))
        return group


class IniLoader(object):
    '''
    Loader to read inventory from an INI-formatted text file.
    '''
    def __init__(self, source, all_group=None, group_filter_re=None, host_filter_re=None):
        self.source = source
        self.source_dir = os.path.dirname(self.source)
        self.inventory = FileMemInventory(
            self.source_dir, all_group,
            group_filter_re=group_filter_re, host_filter_re=host_filter_re)

    def get_host_names_from_entry(self, name):
        '''
        Given an entry in an Ansible inventory file, return an iterable of
        the resultant host names, accounting for expansion patterns.
        Examples:
        web1.server.com -> web1.server.com
        web[1:2].server.com -> web1.server.com, web2.server.com
        '''
        def iternest(*args):
            if args:
                for i in args[0]:
                    for j in iternest(*args[1:]):
                        yield ''.join([str(i), j])
            else:
                yield ''
        if ipv6_port_re.match(name):
            yield self.inventory.get_host(name)
            return
        pattern_re = re.compile(r'(\[(?:(?:\d+\:\d+)|(?:[A-Za-z]\:[A-Za-z]))(?:\:\d+)??\])')
        iters = []
        for s in re.split(pattern_re, name):
            if re.match(pattern_re, s):
                start, end, step = (s[1:-1] + ':1').split(':')[:3]
                mapfunc = str
                if start in string.ascii_letters:
                    istart = string.ascii_letters.index(start)
                    iend = string.ascii_letters.index(end) + 1
                    if istart >= iend:
                        raise ValueError('invalid host range specified')
                    seq = string.ascii_letters[istart:iend:int(step)]
                else:
                    if start[0] == '0' and len(start) > 1:
                        if len(start) != len(end):
                            raise ValueError('invalid host range specified')
                        mapfunc = lambda x: str(x).zfill(len(start))
                    seq = xrange(int(start), int(end) + 1, int(step))
                iters.append(map(mapfunc, seq))
            elif re.search(r'[\[\]]', s):
                raise ValueError('invalid host range specified')
            elif s:
                iters.append([s])
        for iname in iternest(*iters):
            yield self.inventory.get_host(iname)

    @staticmethod
    def file_line_iterable(filename):
        return file(filename, 'r')

    def load(self):
        logger.info('Reading INI source: %s', self.source)
        group = self.inventory.all_group
        input_mode = 'host'
        for line in self.file_line_iterable(self.source):
            line = line.split('#')[0].strip()
            if not line:
                continue
            elif line.startswith('[') and line.endswith(']'):
                # Mode change, possible new group name
                line = line[1:-1].strip()
                if line.endswith(':vars'):
                    input_mode = 'vars'
                    line = line[:-5]
                elif line.endswith(':children'):
                    input_mode = 'children'
                    line = line[:-9]
                else:
                    input_mode = 'host'
                group = self.inventory.get_group(line)
            elif group:
                # If group is None, we are skipping this group and shouldn't
                # capture any children/variables/hosts under it.
                # Add hosts with inline variables, or variables/children to
                # an existing group.
                tokens = shlex.split(line)
                if input_mode == 'host':
                    for host in self.get_host_names_from_entry(tokens[0]):
                        if not host:
                            continue
                        if len(tokens) > 1:
                            for t in tokens[1:]:
                                k,v = t.split('=', 1)
                                host.variables[k] = v
                        group.add_host(host)
                elif input_mode == 'children':
                    self.inventory.get_group(line, group)
                elif input_mode == 'vars':
                    for t in tokens:
                        k, v = t.split('=', 1)
                        group.variables[k] = v
        return self.inventory


def load_inventory_source(source, all_group=None, group_filter_re=None,
                          host_filter_re=None, exclude_empty_groups=False):
    '''
    Load inventory from given source directory or file.
    '''
    original_all_group = all_group
    if not os.path.exists(source):
        raise IOError('Source does not exist: %s' % source)
    source = os.path.join(os.getcwd(), os.path.dirname(source),
                          os.path.basename(source))
    source = os.path.normpath(os.path.abspath(source))
    if os.path.isdir(source):
        all_group = all_group or MemGroup('all')
        for filename in glob.glob(os.path.join(source, '*')):
            if filename.endswith(".ini") or os.path.isdir(filename):
                continue
            load_inventory_source(filename, all_group, group_filter_re,
                                  host_filter_re)
    elif os.access(source, os.X_OK):
        raise NotImplementedError(
            'Source has been marked as executable, but script-based sources '
            'are not supported by the legacy file import plugin. '
            'This problem may be solved by upgrading to use `ansible-inventory`.')
    else:
        all_group = all_group or MemGroup('all', os.path.dirname(source))
        IniLoader(source, all_group, group_filter_re, host_filter_re).load()

    logger.debug('Finished loading from source: %s', source)
    # Exclude groups that are completely empty.
    if original_all_group is None and exclude_empty_groups:
        for name, group in all_group.all_groups.items():
            if not group.children and not group.hosts and not group.variables:
                logger.debug('Removing empty group %s', name)
                for parent in group.parents:
                    if group in parent.children:
                        parent.children.remove(group)
                del all_group.all_groups[name]
    if original_all_group is None:
        logger.info('Loaded %d groups, %d hosts', len(all_group.all_groups),
                    len(all_group.all_hosts))
    return all_group


def parse_args():
    parser = argparse.ArgumentParser(description='Ansible Inventory Import Plugin - Fallback Option')
    parser.add_argument(
        '-i', '--inventory-file', dest='inventory', required=True,
        help="Specify inventory host path (does not support CSV host paths)")
    parser.add_argument(
        '--list', action='store_true', dest='list', default=None, required=True,
        help='Output all hosts info, works as inventory script')
    # --host and --graph and not supported
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    source = args.inventory
    memory_data = load_inventory_source(
        source, group_filter_re=None,
        host_filter_re=None, exclude_empty_groups=False)
    mem_inventory = MemInventory(all_group=memory_data)
    inventory_dict = mem_data_to_dict(mem_inventory)
    print json.dumps(inventory_dict, indent=4)
