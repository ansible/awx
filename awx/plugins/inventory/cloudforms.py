#!/usr/bin/python

'''
CloudForms external inventory script
==================================================
Generates inventory that Ansible can understand by making API request to CloudForms.
Modeled after https://raw.githubusercontent.com/ansible/ansible/stable-1.9/plugins/inventory/ec2.py
jlabocki <at> redhat.com or @jameslabocki on twitter
'''

import os
import argparse
import ConfigParser
import requests
import json

# This disables warnings and is not a good idea, but hey, this is a demo
# http://urllib3.readthedocs.org/en/latest/security.html#disabling-warnings
requests.packages.urllib3.disable_warnings()

class CloudFormsInventory(object):

    def _empty_inventory(self):
        return {"_meta" : {"hostvars" : {}}}

    def __init__(self):
        ''' Main execution path '''

        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = self._empty_inventory()

        # Index of hostname (address) to instance ID
        self.index = {}

        # Read CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Get Hosts
        if self.args.list:
            self.get_hosts()

        # This doesn't exist yet and needs to be added
        if self.args.host:
            data2 = { }
            print json.dumps(data2, indent=2)

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on CloudForms')
        parser.add_argument('--list', action='store_true', default=False,
                           help='List instances (default: False)')
        parser.add_argument('--host', action='store',
                           help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def read_settings(self):
        ''' Reads the settings from the cloudforms.ini file '''

        config = ConfigParser.SafeConfigParser()
        config_paths = [
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'cloudforms.ini'),
            "/opt/rh/cloudforms.ini",
        ]

        env_value = os.environ.get('CLOUDFORMS_INI_PATH')
        if env_value is not None:
            config_paths.append(os.path.expanduser(os.path.expandvars(env_value)))

        config.read(config_paths)

        # Version
        if config.has_option('cloudforms', 'version'):
            self.cloudforms_version = config.get('cloudforms', 'version')
        else:
            self.cloudforms_version = "none"

        # CloudForms Endpoint
        if config.has_option('cloudforms', 'hostname'):
            self.cloudforms_hostname = config.get('cloudforms', 'hostname')
        else:
            self.cloudforms_hostname = None

        # CloudForms Username
        if config.has_option('cloudforms', 'username'):
            self.cloudforms_username = config.get('cloudforms', 'username')
        else:
            self.cloudforms_username = "none"

        # CloudForms Password
        if config.has_option('cloudforms', 'password'):
            self.cloudforms_password = config.get('cloudforms', 'password')
        else:
            self.cloudforms_password = "none"

    def get_hosts(self):
        ''' Gets host from CloudForms '''
        r = requests.get("https://" + self.cloudforms_hostname + "/api/vms?expand=resources&attributes=name,power_state", auth=(self.cloudforms_username,self.cloudforms_password), verify=False)

        obj = r.json()

        #Remove objects that don't matter
        del obj["count"]
        del obj["subcount"]
        del obj["name"]

        #Create a new list to grab VMs with power_state on to add to a new list
        #I'm sure there is a cleaner way to do this
        newlist = []
        getnext = False
        for x in obj.items():
            for y in x[1]:
                for z in y.items():
                    if getnext == True:
                        newlist.append(z[1])
                        getnext = False
                    if ( z[0] == "power_state" and z[1] == "on" ):
                        getnext = True
        newdict = {'hosts': newlist}
        newdict2 = {'Dynamic_CloudForms': newdict}
        print json.dumps(newdict2, indent=2)

# Run the script
CloudFormsInventory()
