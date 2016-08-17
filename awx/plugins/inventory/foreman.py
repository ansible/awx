#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2016 Guido Günther <agx@sigxcpu.org>
#
# This script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with it.  If not, see <http://www.gnu.org/licenses/>.
#
# This is somewhat based on cobbler inventory

import argparse
import ConfigParser
import copy
import os
import re
from time import time
import requests
from requests.auth import HTTPBasicAuth

try:
    import json
except ImportError:
    import simplejson as json


class ForemanInventory(object):
    def __init__(self):
        """ Main execution path """
        self.inventory = dict()  # A list of groups and the hosts in that group
        self.cache = dict()  # Details about hosts in the inventory
        self.params = dict() # Params of each host
        self.facts = dict() # Facts of each host
        self.hostgroups = dict()  # host groups

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Cache
        if self.args.refresh_cache:
            self.update_cache()
        elif not self.is_cache_valid():
            self.update_cache()
        else:
            self.load_inventory_from_cache()
            self.load_params_from_cache()
            self.load_facts_from_cache()
            self.load_cache_from_cache()

        data_to_print = ""

        # Data to print
        if self.args.host:
            data_to_print += self.get_host_info()
        else:
            self.inventory['_meta'] = {'hostvars': {}}
            for hostname in self.cache:
                self.inventory['_meta']['hostvars'][hostname] = {
                    'foreman': self.cache[hostname],
                    'foreman_params': self.params[hostname],
                }
                if self.want_facts:
                    self.inventory['_meta']['hostvars'][hostname]['foreman_facts'] = self.facts[hostname]

            data_to_print += self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def is_cache_valid(self):
        """ Determines if the cache files have expired, or if it is still valid """

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if (os.path.isfile(self.cache_path_inventory) and
                    os.path.isfile(self.cache_path_params) and
                    os.path.isfile(self.cache_path_facts)):
                    return True
        return False

    def read_settings(self):
        """ Reads the settings from the foreman.ini file """

        config = ConfigParser.SafeConfigParser()
        config_paths = [
            "/etc/ansible/foreman.ini",
            os.path.dirname(os.path.realpath(__file__)) + '/foreman.ini',
        ]

        env_value = os.environ.get('FOREMAN_INI_PATH')
        if env_value is not None:
            config_paths.append(os.path.expanduser(os.path.expandvars(env_value)))

        config.read(config_paths)

        # Foreman API related
        self.foreman_url = config.get('foreman', 'url')
        self.foreman_user = config.get('foreman', 'user')
        self.foreman_pw = config.get('foreman', 'password')
        self.foreman_ssl_verify = config.getboolean('foreman', 'ssl_verify')

        # Ansible related
        try:
            group_patterns = config.get('ansible', 'group_patterns')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            group_patterns = "[]"

        self.group_patterns = eval(group_patterns)

        try:
            self.group_prefix = config.get('ansible', 'group_prefix')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            self.group_prefix = "foreman_"

        try:
            self.want_facts = config.getboolean('ansible', 'want_facts')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            self.want_facts = True

        # Cache related
        try:
            cache_path = os.path.expanduser(config.get('cache', 'path'))
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            cache_path = '.'
        (script, ext) = os.path.splitext(os.path.basename(__file__))
        self.cache_path_cache = cache_path + "/%s.cache" % script
        self.cache_path_inventory = cache_path + "/%s.index" % script
        self.cache_path_params = cache_path + "/%s.params" % script
        self.cache_path_facts = cache_path + "/%s.facts" % script
        self.cache_max_age = config.getint('cache', 'max_age')

    def parse_cli_args(self):
        """ Command line argument processing """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on foreman')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to foreman (default: False - use cache files)')
        self.args = parser.parse_args()

    def _get_json(self, url, ignore_errors=None):
        page = 1
        results = []
        while True:
            ret = requests.get(url,
                               auth=HTTPBasicAuth(self.foreman_user, self.foreman_pw),
                               verify=self.foreman_ssl_verify,
                               params={'page': page, 'per_page': 250})
            if ignore_errors and ret.status_code in ignore_errors:
                break
            ret.raise_for_status()
            json = ret.json()
            if not json.has_key('results'):
                return json
            if type(json['results']) == type({}):
                return json['results']
            results = results + json['results']
            if len(results) >= json['total']:
                break
            page += 1
        return results

    def _get_hosts(self):
        return self._get_json("%s/api/v2/hosts" % self.foreman_url)

    def _get_hostgroup_by_id(self, hid):
        if hid not in self.hostgroups:
            url = "%s/api/v2/hostgroups/%s" % (self.foreman_url, hid)
            self.hostgroups[hid] = self._get_json(url)
        return self.hostgroups[hid]

    def _get_all_params_by_id(self, hid):
        url = "%s/api/v2/hosts/%s" % (self.foreman_url, hid)
        ret = self._get_json(url, [404])
        if ret == []: ret = {}
        return ret.get('all_parameters', {})

    def _get_facts_by_id(self, hid):
        url = "%s/api/v2/hosts/%s/facts" % (self.foreman_url, hid)
        return self._get_json(url)

    def _resolve_params(self, host):
        """
        Fetch host params and convert to dict
        """
        params = {}

        for param in self._get_all_params_by_id(host['id']):
            name = param['name']
            params[name] = param['value']

        return params

    def _get_facts(self, host):
        """
        Fetch all host facts of the host
        """
        if not self.want_facts:
            return {}

        ret = self._get_facts_by_id(host['id'])
        if len(ret.values()) == 0:
            facts = {}
        elif len(ret.values()) == 1:
            facts = ret.values()[0]
        else:
            raise ValueError("More than one set of facts returned for '%s'" % host)
        return facts

    def update_cache(self):
        """Make calls to foreman and save the output in a cache"""

        self.groups = dict()
        self.hosts = dict()

        for host in self._get_hosts():
            dns_name = host['name']

            # Create ansible groups for hostgroup, environment, location and organization
            for group in ['hostgroup', 'environment', 'location', 'organization']:
                val = host.get('%s_name' % group)
                if val:
                    safe_key = self.to_safe('%s%s_%s' % (self.group_prefix, group, val.lower()))
                    self.push(self.inventory, safe_key, dns_name)

            for group in ['lifecycle_environment', 'content_view']:
                val = host.get('content_facet_attributes', {}).get('%s_name' % group)
                if val:
                    safe_key = self.to_safe('%s%s_%s' % (self.group_prefix, group, val.lower()))
                    self.push(self.inventory, safe_key, dns_name)

            params = self._resolve_params(host)

            # Ansible groups by parameters in host groups and Foreman host
            # attributes.
            groupby = copy.copy(params)
            for k, v in host.items():
                if isinstance(v, basestring):
                    groupby[k] = self.to_safe(v)
                elif isinstance(v, int):
                    groupby[k] = v

            # The name of the ansible groups is given by group_patterns:
            for pattern in self.group_patterns:
                try:
                    key = pattern.format(**groupby)
                    self.push(self.inventory, key, dns_name)
                except KeyError:
                    pass  # Host not part of this group

            self.cache[dns_name] = host
            self.params[dns_name] = params
            self.facts[dns_name] = self._get_facts(host)
            self.push(self.inventory, 'all', dns_name)

        self.write_to_cache(self.cache, self.cache_path_cache)
        self.write_to_cache(self.inventory, self.cache_path_inventory)
        self.write_to_cache(self.params, self.cache_path_params)
        self.write_to_cache(self.facts, self.cache_path_facts)

    def get_host_info(self):
        """ Get variables about a specific host """

        if not self.cache or len(self.cache) == 0:
            # Need to load index from cache
            self.load_cache_from_cache()

        if self.args.host not in self.cache:
            # try updating the cache
            self.update_cache()

            if self.args.host not in self.cache:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        return self.json_format_dict(self.cache[self.args.host], True)

    def push(self, d, k, v):
        if k in d:
            d[k].append(v)
        else:
            d[k] = [v]

    def load_inventory_from_cache(self):
        """ Reads the index from the cache file sets self.index """

        cache = open(self.cache_path_inventory, 'r')
        json_inventory = cache.read()
        self.inventory = json.loads(json_inventory)

    def load_params_from_cache(self):
        """ Reads the index from the cache file sets self.index """

        cache = open(self.cache_path_params, 'r')
        json_params = cache.read()
        self.params = json.loads(json_params)

    def load_facts_from_cache(self):
        """ Reads the index from the cache file sets self.index """
        if not self.want_facts:
            return
        cache = open(self.cache_path_facts, 'r')
        json_facts = cache.read()
        self.facts = json.loads(json_facts)

    def load_cache_from_cache(self):
        """ Reads the cache from the cache file sets self.cache """

        cache = open(self.cache_path_cache, 'r')
        json_cache = cache.read()
        self.cache = json.loads(json_cache)

    def write_to_cache(self, data, filename):
        """ Writes data in JSON format to a file """
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used as Ansible groups '''
        regex = "[^A-Za-z0-9\_]"
        return re.sub(regex, "_", word.replace(" ", ""))

    def json_format_dict(self, data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

if __name__ == '__main__':
  ForemanInventory()


