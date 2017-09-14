#!/usr/bin/env python

'''
Windows Azure external inventory script
=======================================

Generates inventory that Ansible can understand by making API request to
Windows Azure using the azure python library.

NOTE: This script assumes Ansible is being executed where azure is already
installed.

    pip install azure

Adapted from the ansible Linode plugin by Dan Slimmon.
'''
from __future__ import print_function

# (c) 2013, John Whitbeck
#
# This file is part of Ansible,
#
# Ansible is free software: you can redistribute it and/or modify
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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

# Standard imports
import re
import sys
import argparse
import os
from urlparse import urlparse
from time import time
try:
    import json
except ImportError:
    import simplejson as json

try:
    from azure.servicemanagement import ServiceManagementService
except ImportError as e:
    sys.exit("ImportError: {0}".format(str(e)))

# Imports for ansible
import ConfigParser

class AzureInventory(object):
    def __init__(self):
        """Main execution path."""
        # Inventory grouped by display group
        self.inventory = {}
        # Index of deployment name -> host
        self.index = {}
        self.host_metadata = {}

        # Cache setting defaults.
        # These can be overridden in settings (see `read_settings`).
        cache_dir = os.path.expanduser('~')
        self.cache_path_cache = os.path.join(cache_dir, '.ansible-azure.cache')
        self.cache_path_index = os.path.join(cache_dir, '.ansible-azure.index')
        self.cache_max_age = 0

        # Read settings and parse CLI arguments
        self.read_settings()
        self.read_environment()
        self.parse_cli_args()

        # Initialize Azure ServiceManagementService
        self.sms = ServiceManagementService(self.subscription_id, self.cert_path)

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        if self.args.list_images:
            data_to_print = self.json_format_dict(self.get_images(), True)
        elif self.args.list or self.args.host:
            # Display list of nodes for inventory
            if len(self.inventory) == 0:
                data = json.loads(self.get_inventory_from_cache())
            else:
                data = self.inventory

            if self.args.host:
                data_to_print = self.get_host(self.args.host)
            else:
                # Add the `['_meta']['hostvars']` information.
                hostvars = {}
                if len(data) > 0:
                    for host in set([h for hosts in data.values() for h in hosts if h]):
                        hostvars[host] = self.get_host(host, jsonify=False)
                data['_meta'] = {'hostvars': hostvars}

                # JSONify the data.
                data_to_print = self.json_format_dict(data, pretty=True)
        print(data_to_print)

    def get_host(self, hostname, jsonify=True):
        """Return information about the given hostname, based on what
        the Windows Azure API provides.
        """
        if hostname not in self.host_metadata:
            return "No host found: %s" % json.dumps(self.host_metadata)
        if jsonify:
            return json.dumps(self.host_metadata[hostname])
        return self.host_metadata[hostname]

    def get_images(self):
        images = []
        for image in self.sms.list_os_images():
            if str(image.label).lower().find(self.args.list_images.lower()) >= 0:
                images.append(vars(image))
        return json.loads(json.dumps(images, default=lambda o: o.__dict__))

    def is_cache_valid(self):
        """Determines if the cache file has expired, or if it is still valid."""
        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True
        return False

    def read_settings(self):
        """Reads the settings from the .ini file."""
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/windows_azure.ini')

        # Credentials related
        if config.has_option('azure', 'subscription_id'):
            self.subscription_id = config.get('azure', 'subscription_id')
        if config.has_option('azure', 'cert_path'):
            self.cert_path = config.get('azure', 'cert_path')

        # Cache related
        if config.has_option('azure', 'cache_path'):
            cache_path = os.path.expandvars(os.path.expanduser(config.get('azure', 'cache_path')))
            self.cache_path_cache = os.path.join(cache_path, 'ansible-azure.cache')
            self.cache_path_index = os.path.join(cache_path, 'ansible-azure.index')
        if config.has_option('azure', 'cache_max_age'):
            self.cache_max_age = config.getint('azure', 'cache_max_age')

    def read_environment(self):
        ''' Reads the settings from environment variables '''
        # Credentials
        if os.getenv("AZURE_SUBSCRIPTION_ID"):
            self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        if os.getenv("AZURE_CERT_PATH"):
            self.cert_path = os.getenv("AZURE_CERT_PATH")

    def parse_cli_args(self):
        """Command line argument processing"""
        parser = argparse.ArgumentParser(
            description='Produce an Ansible Inventory file based on Azure',
        )
        parser.add_argument('--list', action='store_true', default=True,
                            help='List nodes (default: True)')
        parser.add_argument('--list-images', action='store',
                            help='Get all available images.')
        parser.add_argument('--refresh-cache',
            action='store_true', default=False,
            help='Force refresh of thecache by making API requests to Azure '
                 '(default: False - use cache files)',
        )
        parser.add_argument('--host', action='store',
                            help='Get all information about an instance.')
        self.args = parser.parse_args()

    def do_api_calls_update_cache(self):
        """Do API calls, and save data in cache files."""
        self.add_cloud_services()
        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def add_cloud_services(self):
        """Makes an Azure API call to get the list of cloud services."""
        try:
            for cloud_service in self.sms.list_hosted_services():
                self.add_deployments(cloud_service)
        except Exception as e:
            sys.exit("Error: Failed to access cloud services - {0}".format(str(e)))

    def add_deployments(self, cloud_service):
        """Makes an Azure API call to get the list of virtual machines
        associated with a cloud service.
        """
        try:
            for deployment in self.sms.get_hosted_service_properties(cloud_service.service_name,embed_detail=True).deployments.deployments:
                self.add_deployment(cloud_service, deployment)
        except Exception as e:
            sys.exit("Error: Failed to access deployments - {0}".format(str(e)))

    def add_deployment(self, cloud_service, deployment):
        """Adds a deployment to the inventory and index"""
        for role in deployment.role_instance_list.role_instances:
            try:
                # Default port 22 unless port found with name 'SSH'
                port = '22'
                for ie in role.instance_endpoints.instance_endpoints:
                    if ie.name == 'SSH':
                        port = ie.public_port
                        break
            except AttributeError as e:
                pass
            finally:
                self.add_instance(role.instance_name, deployment, port, cloud_service, role.instance_status)

    def add_instance(self, hostname, deployment, ssh_port, cloud_service, status):
        """Adds an instance to the inventory and index"""

        dest = urlparse(deployment.url).hostname

        # Add to index
        self.index[hostname] = deployment.name

        self.host_metadata[hostname] = dict(ansible_ssh_host=dest,
                                            ansible_ssh_port=int(ssh_port),
                                            instance_status=status,
                                            private_id=deployment.private_id)

        # List of all azure deployments
        self.push(self.inventory, "azure", hostname)

        # Inventory: Group by service name
        self.push(self.inventory, self.to_safe(cloud_service.service_name), hostname)

        if int(ssh_port) == 22:
            self.push(self.inventory, "Cloud_services", hostname)

        # Inventory: Group by region
        self.push(self.inventory, self.to_safe(cloud_service.hosted_service_properties.location), hostname)

    def push(self, my_dict, key, element):
        """Pushed an element onto an array that may not have been defined in the dict."""
        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def get_inventory_from_cache(self):
        """Reads the inventory from the cache file and returns it as a JSON object."""
        cache = open(self.cache_path_cache, 'r')
        json_inventory = cache.read()
        return json_inventory

    def load_index_from_cache(self):
        """Reads the index from the cache file and sets self.index."""
        cache = open(self.cache_path_index, 'r')
        json_index = cache.read()
        self.index = json.loads(json_index)

    def write_to_cache(self, data, filename):
        """Writes data in JSON format to a file."""
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        """Escapes any characters that would be invalid in an ansible group name."""
        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        """Converts a dict to a JSON object and dumps it as a formatted string."""
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


AzureInventory()
