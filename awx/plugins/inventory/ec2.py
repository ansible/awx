#!/usr/bin/env python

'''
EC2 external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
AWS EC2 using the Boto library.

NOTE: This script assumes Ansible is being executed where the environment
variables needed for Boto have already been set:
    export AWS_ACCESS_KEY_ID='AK123'
    export AWS_SECRET_ACCESS_KEY='abc123'

optional region environement variable if region is 'auto'

This script also assumes there is an ec2.ini file alongside it.  To specify a
different path to ec2.ini, define the EC2_INI_PATH environment variable:

    export EC2_INI_PATH=/path/to/my_ec2.ini

If you're using eucalyptus you need to set the above variables and
you need to define:

    export EC2_URL=http://hostname_of_your_cc:port/services/Eucalyptus

If you're using boto profiles (requires boto>=2.24.0) you can choose a profile
using the --boto-profile command line argument (e.g. ec2.py --boto-profile prod) or using
the AWS_PROFILE variable:

    AWS_PROFILE=prod ansible-playbook -i ec2.py myplaybook.yml

For more details, see: http://docs.pythonboto.org/en/latest/boto_config_tut.html

When run against a specific host, this script returns the following variables:
 - ec2_ami_launch_index
 - ec2_architecture
 - ec2_association
 - ec2_attachTime
 - ec2_attachment
 - ec2_attachmentId
 - ec2_block_devices
 - ec2_client_token
 - ec2_deleteOnTermination
 - ec2_description
 - ec2_deviceIndex
 - ec2_dns_name
 - ec2_eventsSet
 - ec2_group_name
 - ec2_hypervisor
 - ec2_id
 - ec2_image_id
 - ec2_instanceState
 - ec2_instance_type
 - ec2_ipOwnerId
 - ec2_ip_address
 - ec2_item
 - ec2_kernel
 - ec2_key_name
 - ec2_launch_time
 - ec2_monitored
 - ec2_monitoring
 - ec2_networkInterfaceId
 - ec2_ownerId
 - ec2_persistent
 - ec2_placement
 - ec2_platform
 - ec2_previous_state
 - ec2_private_dns_name
 - ec2_private_ip_address
 - ec2_publicIp
 - ec2_public_dns_name
 - ec2_ramdisk
 - ec2_reason
 - ec2_region
 - ec2_requester_id
 - ec2_root_device_name
 - ec2_root_device_type
 - ec2_security_group_ids
 - ec2_security_group_names
 - ec2_shutdown_state
 - ec2_sourceDestCheck
 - ec2_spot_instance_request_id
 - ec2_state
 - ec2_state_code
 - ec2_state_reason
 - ec2_status
 - ec2_subnet_id
 - ec2_tenancy
 - ec2_virtualization_type
 - ec2_vpc_id

These variables are pulled out of a boto.ec2.instance object. There is a lack of
consistency with variable spellings (camelCase and underscores) since this
just loops through all variables the object exposes. It is preferred to use the
ones with underscores when multiple exist.

In addition, if an instance has AWS Tags associated with it, each tag is a new
variable named:
 - ec2_tag_[Key] = [Value]

Security groups are comma-separated in 'ec2_security_group_ids' and
'ec2_security_group_names'.
'''
from __future__ import print_function

# (c) 2012, Peter Sankauskas
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

import sys
import os
import argparse
import re
from time import time
import boto
from boto import ec2
from boto import rds
from boto import elasticache
from boto import route53
import six

from ansible.module_utils import ec2 as ec2_utils

HAS_BOTO3 = False
try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    pass

from six.moves import configparser
from collections import defaultdict

try:
    import json
except ImportError:
    import simplejson as json


class Ec2Inventory(object):

    def _empty_inventory(self):
        return {"_meta" : {"hostvars" : {}}}

    def __init__(self):
        ''' Main execution path '''

        # Inventory grouped by instance IDs, tags, security groups, regions,
        # and availability zones
        self.inventory = self._empty_inventory()

        self.aws_account_id = None

        # Index of hostname (address) to instance ID
        self.index = {}

        # Boto profile to use (if any)
        self.boto_profile = None

        # AWS credentials.
        self.credentials = {}

        # Read settings and parse CLI arguments
        self.parse_cli_args()
        self.read_settings()

        # Make sure that profile_name is not passed at all if not set
        # as pre 2.24 boto will fall over otherwise
        if self.boto_profile:
            if not hasattr(boto.ec2.EC2Connection, 'profile_name'):
                self.fail_with_error("boto version must be >= 2.24 to use profile")

        # Cache
        if self.args.refresh_cache:
            self.do_api_calls_update_cache()
        elif not self.is_cache_valid():
            self.do_api_calls_update_cache()

        # Data to print
        if self.args.host:
            data_to_print = self.get_host_info()

        elif self.args.list:
            # Display list of instances for inventory
            if self.inventory == self._empty_inventory():
                data_to_print = self.get_inventory_from_cache()
            else:
                data_to_print = self.json_format_dict(self.inventory, True)

        print(data_to_print)


    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_index):
                    return True

        return False


    def read_settings(self):
        ''' Reads the settings from the ec2.ini file '''

        scriptbasename = __file__
        scriptbasename = os.path.basename(scriptbasename)
        scriptbasename = scriptbasename.replace('.py', '')

        defaults = {'ec2': {
            'ini_path': os.path.join(os.path.dirname(__file__), '%s.ini' % scriptbasename)
            }
        }

        if six.PY3:
            config = configparser.ConfigParser()
        else:
            config = configparser.SafeConfigParser()
        ec2_ini_path = os.environ.get('EC2_INI_PATH', defaults['ec2']['ini_path'])
        ec2_ini_path = os.path.expanduser(os.path.expandvars(ec2_ini_path))
        config.read(ec2_ini_path)

        # is eucalyptus?
        self.eucalyptus_host = None
        self.eucalyptus = False
        if config.has_option('ec2', 'eucalyptus'):
            self.eucalyptus = config.getboolean('ec2', 'eucalyptus')
        if self.eucalyptus and config.has_option('ec2', 'eucalyptus_host'):
            self.eucalyptus_host = config.get('ec2', 'eucalyptus_host')

        # Regions
        self.regions = []
        configRegions = config.get('ec2', 'regions')
        configRegions_exclude = config.get('ec2', 'regions_exclude')
        if (configRegions == 'all'):
            if self.eucalyptus_host:
                self.regions.append(boto.connect_euca(host=self.eucalyptus_host).region.name, **self.credentials)
            else:
                for regionInfo in ec2.regions():
                    if regionInfo.name not in configRegions_exclude:
                        self.regions.append(regionInfo.name)
        else:
            self.regions = configRegions.split(",")
        if 'auto' in self.regions:
            env_region = os.environ.get('AWS_REGION')
            if env_region is None:
                env_region = os.environ.get('AWS_DEFAULT_REGION')
            self.regions = [ env_region ]

        # Destination addresses
        self.destination_variable = config.get('ec2', 'destination_variable')
        self.vpc_destination_variable = config.get('ec2', 'vpc_destination_variable')

        if config.has_option('ec2', 'hostname_variable'):
            self.hostname_variable = config.get('ec2', 'hostname_variable')
        else:
            self.hostname_variable = None

        if config.has_option('ec2', 'destination_format') and \
           config.has_option('ec2', 'destination_format_tags'):
            self.destination_format = config.get('ec2', 'destination_format')
            self.destination_format_tags = config.get('ec2', 'destination_format_tags').split(',')
        else:
            self.destination_format = None
            self.destination_format_tags = None

        # Route53
        self.route53_enabled = config.getboolean('ec2', 'route53')
        if config.has_option('ec2', 'route53_hostnames'):
            self.route53_hostnames = config.get('ec2', 'route53_hostnames')
        else:
            self.route53_hostnames = None
        self.route53_excluded_zones = []
        if config.has_option('ec2', 'route53_excluded_zones'):
            self.route53_excluded_zones.extend(
                config.get('ec2', 'route53_excluded_zones', '').split(','))

        # Include RDS instances?
        self.rds_enabled = True
        if config.has_option('ec2', 'rds'):
            self.rds_enabled = config.getboolean('ec2', 'rds')

        # Include RDS cluster instances?
        if config.has_option('ec2', 'include_rds_clusters'):
            self.include_rds_clusters = config.getboolean('ec2', 'include_rds_clusters')
        else:
            self.include_rds_clusters = False

        # Include ElastiCache instances?
        self.elasticache_enabled = True
        if config.has_option('ec2', 'elasticache'):
            self.elasticache_enabled = config.getboolean('ec2', 'elasticache')

        # Return all EC2 instances?
        if config.has_option('ec2', 'all_instances'):
            self.all_instances = config.getboolean('ec2', 'all_instances')
        else:
            self.all_instances = False

        # Instance states to be gathered in inventory. Default is 'running'.
        # Setting 'all_instances' to 'yes' overrides this option.
        ec2_valid_instance_states = [
            'pending',
            'running',
            'shutting-down',
            'terminated',
            'stopping',
            'stopped'
        ]
        self.ec2_instance_states = []
        if self.all_instances:
            self.ec2_instance_states = ec2_valid_instance_states
        elif config.has_option('ec2', 'instance_states'):
            for instance_state in config.get('ec2', 'instance_states').split(','):
                instance_state = instance_state.strip()
                if instance_state not in ec2_valid_instance_states:
                    continue
                self.ec2_instance_states.append(instance_state)
        else:
            self.ec2_instance_states = ['running']

        # Return all RDS instances? (if RDS is enabled)
        if config.has_option('ec2', 'all_rds_instances') and self.rds_enabled:
            self.all_rds_instances = config.getboolean('ec2', 'all_rds_instances')
        else:
            self.all_rds_instances = False

        # Return all ElastiCache replication groups? (if ElastiCache is enabled)
        if config.has_option('ec2', 'all_elasticache_replication_groups') and self.elasticache_enabled:
            self.all_elasticache_replication_groups = config.getboolean('ec2', 'all_elasticache_replication_groups')
        else:
            self.all_elasticache_replication_groups = False

        # Return all ElastiCache clusters? (if ElastiCache is enabled)
        if config.has_option('ec2', 'all_elasticache_clusters') and self.elasticache_enabled:
            self.all_elasticache_clusters = config.getboolean('ec2', 'all_elasticache_clusters')
        else:
            self.all_elasticache_clusters = False

        # Return all ElastiCache nodes? (if ElastiCache is enabled)
        if config.has_option('ec2', 'all_elasticache_nodes') and self.elasticache_enabled:
            self.all_elasticache_nodes = config.getboolean('ec2', 'all_elasticache_nodes')
        else:
            self.all_elasticache_nodes = False

        # boto configuration profile (prefer CLI argument then environment variables then config file)
        self.boto_profile = self.args.boto_profile or os.environ.get('AWS_PROFILE')
        if config.has_option('ec2', 'boto_profile') and not self.boto_profile:
            self.boto_profile = config.get('ec2', 'boto_profile')

        # AWS credentials (prefer environment variables)
        if not (self.boto_profile or os.environ.get('AWS_ACCESS_KEY_ID') or
                os.environ.get('AWS_PROFILE')):
            if config.has_option('credentials', 'aws_access_key_id'):
                aws_access_key_id = config.get('credentials', 'aws_access_key_id')
            else:
                aws_access_key_id = None
            if config.has_option('credentials', 'aws_secret_access_key'):
                aws_secret_access_key = config.get('credentials', 'aws_secret_access_key')
            else:
                aws_secret_access_key = None
            if config.has_option('credentials', 'aws_security_token'):
                aws_security_token = config.get('credentials', 'aws_security_token')
            else:
                aws_security_token = None
            if aws_access_key_id:
                self.credentials = {
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key
                }
                if aws_security_token:
                    self.credentials['security_token'] = aws_security_token

        # Cache related
        cache_dir = os.path.expanduser(config.get('ec2', 'cache_path'))
        if self.boto_profile:
            cache_dir = os.path.join(cache_dir, 'profile_' + self.boto_profile)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        cache_name = 'ansible-ec2'
        cache_id = self.boto_profile or os.environ.get('AWS_ACCESS_KEY_ID', self.credentials.get('aws_access_key_id'))
        if cache_id:
            cache_name = '%s-%s' % (cache_name, cache_id)
        self.cache_path_cache = os.path.join(cache_dir, "%s.cache" % cache_name)
        self.cache_path_index = os.path.join(cache_dir, "%s.index" % cache_name)
        self.cache_max_age = config.getint('ec2', 'cache_max_age')

        if config.has_option('ec2', 'expand_csv_tags'):
            self.expand_csv_tags = config.getboolean('ec2', 'expand_csv_tags')
        else:
            self.expand_csv_tags = False

        # Configure nested groups instead of flat namespace.
        if config.has_option('ec2', 'nested_groups'):
            self.nested_groups = config.getboolean('ec2', 'nested_groups')
        else:
            self.nested_groups = False

        # Replace dash or not in group names
        if config.has_option('ec2', 'replace_dash_in_groups'):
            self.replace_dash_in_groups = config.getboolean('ec2', 'replace_dash_in_groups')
        else:
            self.replace_dash_in_groups = True

        # Configure which groups should be created.
        group_by_options = [
            'group_by_instance_id',
            'group_by_region',
            'group_by_availability_zone',
            'group_by_ami_id',
            'group_by_instance_type',
            'group_by_instance_state',
            'group_by_key_pair',
            'group_by_vpc_id',
            'group_by_security_group',
            'group_by_tag_keys',
            'group_by_tag_none',
            'group_by_route53_names',
            'group_by_rds_engine',
            'group_by_rds_parameter_group',
            'group_by_elasticache_engine',
            'group_by_elasticache_cluster',
            'group_by_elasticache_parameter_group',
            'group_by_elasticache_replication_group',
            'group_by_aws_account',
        ]
        for option in group_by_options:
            if config.has_option('ec2', option):
                setattr(self, option, config.getboolean('ec2', option))
            else:
                setattr(self, option, True)

        # Do we need to just include hosts that match a pattern?
        try:
            pattern_include = config.get('ec2', 'pattern_include')
            if pattern_include and len(pattern_include) > 0:
                self.pattern_include = re.compile(pattern_include)
            else:
                self.pattern_include = None
        except configparser.NoOptionError:
            self.pattern_include = None

        # Do we need to exclude hosts that match a pattern?
        try:
            pattern_exclude = config.get('ec2', 'pattern_exclude')
            if pattern_exclude and len(pattern_exclude) > 0:
                self.pattern_exclude = re.compile(pattern_exclude)
            else:
                self.pattern_exclude = None
        except configparser.NoOptionError:
            self.pattern_exclude = None

        # Do we want to stack multiple filters?
        if config.has_option('ec2', 'stack_filters'):
            self.stack_filters = config.getboolean('ec2', 'stack_filters')
        else:
            self.stack_filters = False

        # Instance filters (see boto and EC2 API docs). Ignore invalid filters.
        self.ec2_instance_filters = defaultdict(list)
        if config.has_option('ec2', 'instance_filters'):

            filters = [f for f in config.get('ec2', 'instance_filters').split(',') if f]

            for instance_filter in filters:
                instance_filter = instance_filter.strip()
                if not instance_filter or '=' not in instance_filter:
                    continue
                filter_key, filter_value = [x.strip() for x in instance_filter.split('=', 1)]
                if not filter_key:
                    continue
                self.ec2_instance_filters[filter_key].append(filter_value)

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on EC2')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                           help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                           help='Force refresh of cache by making API requests to EC2 (default: False - use cache files)')
        parser.add_argument('--profile', '--boto-profile', action='store', dest='boto_profile',
                           help='Use boto profile for connections to EC2')
        self.args = parser.parse_args()


    def do_api_calls_update_cache(self):
        ''' Do API calls to each region, and save data in cache files '''

        if self.route53_enabled:
            self.get_route53_records()

        for region in self.regions:
            self.get_instances_by_region(region)
            if self.rds_enabled:
                self.get_rds_instances_by_region(region)
            if self.elasticache_enabled:
                self.get_elasticache_clusters_by_region(region)
                self.get_elasticache_replication_groups_by_region(region)
            if self.include_rds_clusters:
                self.include_rds_clusters_by_region(region)

        self.write_to_cache(self.inventory, self.cache_path_cache)
        self.write_to_cache(self.index, self.cache_path_index)

    def connect(self, region):
        ''' create connection to api server'''
        if self.eucalyptus:
            conn = boto.connect_euca(host=self.eucalyptus_host, **self.credentials)
            conn.APIVersion = '2010-08-31'
        else:
            conn = self.connect_to_aws(ec2, region)
        return conn

    def boto_fix_security_token_in_profile(self, connect_args):
        ''' monkey patch for boto issue boto/boto#2100 '''
        profile = 'profile ' + self.boto_profile
        if boto.config.has_option(profile, 'aws_security_token'):
            connect_args['security_token'] = boto.config.get(profile, 'aws_security_token')
        return connect_args

    def connect_to_aws(self, module, region):
        connect_args = self.credentials

        # only pass the profile name if it's set (as it is not supported by older boto versions)
        if self.boto_profile:
            connect_args['profile_name'] = self.boto_profile
            self.boto_fix_security_token_in_profile(connect_args)

        conn = module.connect_to_region(region, **connect_args)
        # connect_to_region will fail "silently" by returning None if the region name is wrong or not supported
        if conn is None:
            self.fail_with_error("region name: %s likely not supported, or AWS is down.  connection to region failed." % region)
        return conn

    def get_instances_by_region(self, region):
        ''' Makes an AWS EC2 API call to the list of instances in a particular
        region '''

        try:
            conn = self.connect(region)
            reservations = []
            if self.ec2_instance_filters:
                if self.stack_filters:
                    filters_dict = {}
                    for filter_key, filter_values in self.ec2_instance_filters.items():
                        filters_dict[filter_key] = filter_values
                    reservations.extend(conn.get_all_instances(filters = filters_dict))
                else:
                    for filter_key, filter_values in self.ec2_instance_filters.items():
                        reservations.extend(conn.get_all_instances(filters = { filter_key : filter_values }))
            else:
                reservations = conn.get_all_instances()

            # Pull the tags back in a second step
            # AWS are on record as saying that the tags fetched in the first `get_all_instances` request are not
            # reliable and may be missing, and the only way to guarantee they are there is by calling `get_all_tags`
            instance_ids = []
            for reservation in reservations:
                instance_ids.extend([instance.id for instance in reservation.instances])

            max_filter_value = 199
            tags = []
            for i in range(0, len(instance_ids), max_filter_value):
                tags.extend(conn.get_all_tags(filters={'resource-type': 'instance', 'resource-id': instance_ids[i:i+max_filter_value]}))

            tags_by_instance_id = defaultdict(dict)
            for tag in tags:
                tags_by_instance_id[tag.res_id][tag.name] = tag.value

            if (not self.aws_account_id) and reservations:
                self.aws_account_id = reservations[0].owner_id

            for reservation in reservations:
                for instance in reservation.instances:
                    instance.tags = tags_by_instance_id[instance.id]
                    self.add_instance(instance, region)

        except boto.exception.BotoServerError as e:
            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            else:
                backend = 'Eucalyptus' if self.eucalyptus else 'AWS'
                error = "Error connecting to %s backend.\n%s" % (backend, e.message)
            self.fail_with_error(error, 'getting EC2 instances')

    def get_rds_instances_by_region(self, region):
        ''' Makes an AWS API call to the list of RDS instances in a particular
        region '''

        try:
            conn = self.connect_to_aws(rds, region)
            if conn:
                marker = None
                while True:
                    instances = conn.get_all_dbinstances(marker=marker)
                    marker = instances.marker
                    for instance in instances:
                        self.add_rds_instance(instance, region)
                    if not marker:
                        break
        except boto.exception.BotoServerError as e:
            error = e.reason

            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            if not e.reason == "Forbidden":
                error = "Looks like AWS RDS is down:\n%s" % e.message
            self.fail_with_error(error, 'getting RDS instances')

    def include_rds_clusters_by_region(self, region):
        if not HAS_BOTO3:
            self.fail_with_error("Working with RDS clusters requires boto3 - please install boto3 and try again",
                                 "getting RDS clusters")

        client = ec2_utils.boto3_inventory_conn('client', 'rds', region, **self.credentials)

        marker, clusters = '', []
        while marker is not None:
            resp = client.describe_db_clusters(Marker=marker)
            clusters.extend(resp["DBClusters"])
            marker = resp.get('Marker', None)

        account_id = boto.connect_iam().get_user().arn.split(':')[4]
        c_dict = {}
        for c in clusters:
            # remove these datetime objects as there is no serialisation to json
            # currently in place and we don't need the data yet
            if 'EarliestRestorableTime' in c:
                del c['EarliestRestorableTime']
            if 'LatestRestorableTime' in c:
                del c['LatestRestorableTime']

            if self.ec2_instance_filters == {}:
                matches_filter = True
            else:
                matches_filter = False

            try:
                # arn:aws:rds:<region>:<account number>:<resourcetype>:<name>
                tags = client.list_tags_for_resource(
                    ResourceName='arn:aws:rds:' + region + ':' + account_id + ':cluster:' + c['DBClusterIdentifier'])
                c['Tags'] = tags['TagList']

                if self.ec2_instance_filters:
                    for filter_key, filter_values in self.ec2_instance_filters.items():
                        # get AWS tag key e.g. tag:env will be 'env'
                        tag_name = filter_key.split(":", 1)[1]
                        # Filter values is a list (if you put multiple values for the same tag name)
                        matches_filter = any(d['Key'] == tag_name and d['Value'] in filter_values for d in c['Tags'])

                        if matches_filter:
                            # it matches a filter, so stop looking for further matches
                            break

            except Exception as e:
                if e.message.find('DBInstanceNotFound') >= 0:
                    # AWS RDS bug (2016-01-06) means deletion does not fully complete and leave an 'empty' cluster.
                    # Ignore errors when trying to find tags for these
                    pass

            # ignore empty clusters caused by AWS bug
            if len(c['DBClusterMembers']) == 0:
                continue
            elif matches_filter:
                c_dict[c['DBClusterIdentifier']] = c

        self.inventory['db_clusters'] = c_dict

    def get_elasticache_clusters_by_region(self, region):
        ''' Makes an AWS API call to the list of ElastiCache clusters (with
        nodes' info) in a particular region.'''

        # ElastiCache boto module doesn't provide a get_all_intances method,
        # that's why we need to call describe directly (it would be called by
        # the shorthand method anyway...)
        try:
            conn = self.connect_to_aws(elasticache, region)
            if conn:
                # show_cache_node_info = True
                # because we also want nodes' information
                response = conn.describe_cache_clusters(None, None, None, True)

        except boto.exception.BotoServerError as e:
            error = e.reason

            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            if not e.reason == "Forbidden":
                error = "Looks like AWS ElastiCache is down:\n%s" % e.message
            self.fail_with_error(error, 'getting ElastiCache clusters')

        try:
            # Boto also doesn't provide wrapper classes to CacheClusters or
            # CacheNodes. Because of that we can't make use of the get_list
            # method in the AWSQueryConnection. Let's do the work manually
            clusters = response['DescribeCacheClustersResponse']['DescribeCacheClustersResult']['CacheClusters']

        except KeyError as e:
            error = "ElastiCache query to AWS failed (unexpected format)."
            self.fail_with_error(error, 'getting ElastiCache clusters')

        for cluster in clusters:
            self.add_elasticache_cluster(cluster, region)

    def get_elasticache_replication_groups_by_region(self, region):
        ''' Makes an AWS API call to the list of ElastiCache replication groups
        in a particular region.'''

        # ElastiCache boto module doesn't provide a get_all_intances method,
        # that's why we need to call describe directly (it would be called by
        # the shorthand method anyway...)
        try:
            conn = self.connect_to_aws(elasticache, region)
            if conn:
                response = conn.describe_replication_groups()

        except boto.exception.BotoServerError as e:
            error = e.reason

            if e.error_code == 'AuthFailure':
                error = self.get_auth_error_message()
            if not e.reason == "Forbidden":
                error = "Looks like AWS ElastiCache [Replication Groups] is down:\n%s" % e.message
            self.fail_with_error(error, 'getting ElastiCache clusters')

        try:
            # Boto also doesn't provide wrapper classes to ReplicationGroups
            # Because of that we can't make use of the get_list method in the
            # AWSQueryConnection. Let's do the work manually
            replication_groups = response['DescribeReplicationGroupsResponse']['DescribeReplicationGroupsResult']['ReplicationGroups']

        except KeyError as e:
            error = "ElastiCache [Replication Groups] query to AWS failed (unexpected format)."
            self.fail_with_error(error, 'getting ElastiCache clusters')

        for replication_group in replication_groups:
            self.add_elasticache_replication_group(replication_group, region)

    def get_auth_error_message(self):
        ''' create an informative error message if there is an issue authenticating'''
        errors = ["Authentication error retrieving ec2 inventory."]
        if None in [os.environ.get('AWS_ACCESS_KEY_ID'), os.environ.get('AWS_SECRET_ACCESS_KEY')]:
            errors.append(' - No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY environment vars found')
        else:
            errors.append(' - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment vars found but may not be correct')

        boto_paths = ['/etc/boto.cfg', '~/.boto', '~/.aws/credentials']
        boto_config_found = list(p for p in boto_paths if os.path.isfile(os.path.expanduser(p)))
        if len(boto_config_found) > 0:
            errors.append(" - Boto configs found at '%s', but the credentials contained may not be correct" % ', '.join(boto_config_found))
        else:
            errors.append(" - No Boto config found at any expected location '%s'" % ', '.join(boto_paths))

        return '\n'.join(errors)

    def fail_with_error(self, err_msg, err_operation=None):
        '''log an error to std err for ansible-playbook to consume and exit'''
        if err_operation:
            err_msg = 'ERROR: "{err_msg}", while: {err_operation}'.format(
                err_msg=err_msg, err_operation=err_operation)
        sys.stderr.write(err_msg)
        sys.exit(1)

    def get_instance(self, region, instance_id):
        conn = self.connect(region)

        reservations = conn.get_all_instances([instance_id])
        for reservation in reservations:
            for instance in reservation.instances:
                return instance

    def add_instance(self, instance, region):
        ''' Adds an instance to the inventory and index, as long as it is
        addressable '''

        # Only return instances with desired instance states
        if instance.state not in self.ec2_instance_states:
            return

        # Select the best destination address
        if self.destination_format and self.destination_format_tags:
            dest = self.destination_format.format(*[ getattr(instance, 'tags').get(tag, '') for tag in self.destination_format_tags ])
        elif instance.subnet_id:
            dest = getattr(instance, self.vpc_destination_variable, None)
            if dest is None:
                dest = getattr(instance, 'tags').get(self.vpc_destination_variable, None)
        else:
            dest = getattr(instance, self.destination_variable, None)
            if dest is None:
                dest = getattr(instance, 'tags').get(self.destination_variable, None)

        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Set the inventory name
        hostname = None
        if self.hostname_variable:
            if self.hostname_variable.startswith('tag_'):
                hostname = instance.tags.get(self.hostname_variable[4:], None)
            else:
                hostname = getattr(instance, self.hostname_variable)

        # set the hostname from route53
        if self.route53_enabled and self.route53_hostnames:
            route53_names = self.get_instance_route53_names(instance)
            for name in route53_names:
                if name.endswith(self.route53_hostnames):
                    hostname = name

        # If we can't get a nice hostname, use the destination address
        if not hostname:
            hostname = dest
        # to_safe strips hostname characters like dots, so don't strip route53 hostnames
        elif self.route53_enabled and self.route53_hostnames and hostname.endswith(self.route53_hostnames):
            hostname = hostname.lower()
        else:
            hostname = self.to_safe(hostname).lower()

        # if we only want to include hosts that match a pattern, skip those that don't
        if self.pattern_include and not self.pattern_include.match(hostname):
            return

        # if we need to exclude hosts that match a pattern, skip those
        if self.pattern_exclude and self.pattern_exclude.match(hostname):
            return

        # Add to index
        self.index[hostname] = [region, instance.id]

        # Inventory: Group by instance ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[instance.id] = [hostname]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', instance.id)

        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)

        # Inventory: Group by availability zone
        if self.group_by_availability_zone:
            self.push(self.inventory, instance.placement, hostname)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, instance.placement)
                self.push_group(self.inventory, 'zones', instance.placement)

        # Inventory: Group by Amazon Machine Image (AMI) ID
        if self.group_by_ami_id:
            ami_id = self.to_safe(instance.image_id)
            self.push(self.inventory, ami_id, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'images', ami_id)

        # Inventory: Group by instance type
        if self.group_by_instance_type:
            type_name = self.to_safe('type_' + instance.instance_type)
            self.push(self.inventory, type_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)

        # Inventory: Group by instance state
        if self.group_by_instance_state:
            state_name = self.to_safe('instance_state_' + instance.state)
            self.push(self.inventory, state_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'instance_states', state_name)

        # Inventory: Group by key pair
        if self.group_by_key_pair and instance.key_name:
            key_name = self.to_safe('key_' + instance.key_name)
            self.push(self.inventory, key_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'keys', key_name)

        # Inventory: Group by VPC
        if self.group_by_vpc_id and instance.vpc_id:
            vpc_id_name = self.to_safe('vpc_id_' + instance.vpc_id)
            self.push(self.inventory, vpc_id_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'vpcs', vpc_id_name)

        # Inventory: Group by security group
        if self.group_by_security_group:
            try:
                for group in instance.groups:
                    key = self.to_safe("security_group_" + group.name)
                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)
            except AttributeError:
                self.fail_with_error('\n'.join(['Package boto seems a bit older.',
                                            'Please upgrade boto >= 2.3.0.']))

        # Inventory: Group by AWS account ID
        if self.group_by_aws_account:
            self.push(self.inventory, self.aws_account_id, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'accounts', self.aws_account_id)

        # Inventory: Group by tag keys
        if self.group_by_tag_keys:
            for k, v in instance.tags.items():
                if self.expand_csv_tags and v and ',' in v:
                    values = map(lambda x: x.strip(), v.split(','))
                else:
                    values = [v]

                for v in values:
                    if v:
                        key = self.to_safe("tag_" + k + "=" + v)
                    else:
                        key = self.to_safe("tag_" + k)
                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'tags', self.to_safe("tag_" + k))
                        if v:
                            self.push_group(self.inventory, self.to_safe("tag_" + k), key)

        # Inventory: Group by Route53 domain names if enabled
        if self.route53_enabled and self.group_by_route53_names:
            route53_names = self.get_instance_route53_names(instance)
            for name in route53_names:
                self.push(self.inventory, name, hostname)
                if self.nested_groups:
                    self.push_group(self.inventory, 'route53', name)

        # Global Tag: instances without tags
        if self.group_by_tag_none and len(instance.tags) == 0:
            self.push(self.inventory, 'tag_none', hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'tags', 'tag_none')

        # Global Tag: tag all EC2 instances
        self.push(self.inventory, 'ec2', hostname)

        self.inventory["_meta"]["hostvars"][hostname] = self.get_host_info_dict_from_instance(instance)
        self.inventory["_meta"]["hostvars"][hostname]['ansible_ssh_host'] = dest


    def add_rds_instance(self, instance, region):
        ''' Adds an RDS instance to the inventory and index, as long as it is
        addressable '''

        # Only want available instances unless all_rds_instances is True
        if not self.all_rds_instances and instance.status != 'available':
            return

        # Select the best destination address
        dest = instance.endpoint[0]

        if not dest:
            # Skip instances we cannot address (e.g. private VPC subnet)
            return

        # Set the inventory name
        hostname = None
        if self.hostname_variable:
            if self.hostname_variable.startswith('tag_'):
                hostname = instance.tags.get(self.hostname_variable[4:], None)
            else:
                hostname = getattr(instance, self.hostname_variable)

        # If we can't get a nice hostname, use the destination address
        if not hostname:
            hostname = dest

        hostname = self.to_safe(hostname).lower()

        # Add to index
        self.index[hostname] = [region, instance.id]

        # Inventory: Group by instance ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[instance.id] = [hostname]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', instance.id)

        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)

        # Inventory: Group by availability zone
        if self.group_by_availability_zone:
            self.push(self.inventory, instance.availability_zone, hostname)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, instance.availability_zone)
                self.push_group(self.inventory, 'zones', instance.availability_zone)

        # Inventory: Group by instance type
        if self.group_by_instance_type:
            type_name = self.to_safe('type_' + instance.instance_class)
            self.push(self.inventory, type_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)

        # Inventory: Group by VPC
        if self.group_by_vpc_id and instance.subnet_group and instance.subnet_group.vpc_id:
            vpc_id_name = self.to_safe('vpc_id_' + instance.subnet_group.vpc_id)
            self.push(self.inventory, vpc_id_name, hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'vpcs', vpc_id_name)

        # Inventory: Group by security group
        if self.group_by_security_group:
            try:
                if instance.security_group:
                    key = self.to_safe("security_group_" + instance.security_group.name)
                    self.push(self.inventory, key, hostname)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)

            except AttributeError:
                self.fail_with_error('\n'.join(['Package boto seems a bit older.',
                                            'Please upgrade boto >= 2.3.0.']))


        # Inventory: Group by engine
        if self.group_by_rds_engine:
            self.push(self.inventory, self.to_safe("rds_" + instance.engine), hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'rds_engines', self.to_safe("rds_" + instance.engine))

        # Inventory: Group by parameter group
        if self.group_by_rds_parameter_group:
            self.push(self.inventory, self.to_safe("rds_parameter_group_" + instance.parameter_group.name), hostname)
            if self.nested_groups:
                self.push_group(self.inventory, 'rds_parameter_groups', self.to_safe("rds_parameter_group_" + instance.parameter_group.name))

        # Global Tag: all RDS instances
        self.push(self.inventory, 'rds', hostname)

        self.inventory["_meta"]["hostvars"][hostname] = self.get_host_info_dict_from_instance(instance)
        self.inventory["_meta"]["hostvars"][hostname]['ansible_ssh_host'] = dest

    def add_elasticache_cluster(self, cluster, region):
        ''' Adds an ElastiCache cluster to the inventory and index, as long as
        it's nodes are addressable '''

        # Only want available clusters unless all_elasticache_clusters is True
        if not self.all_elasticache_clusters and cluster['CacheClusterStatus'] != 'available':
            return

        # Select the best destination address
        if 'ConfigurationEndpoint' in cluster and cluster['ConfigurationEndpoint']:
            # Memcached cluster
            dest = cluster['ConfigurationEndpoint']['Address']
            is_redis = False
        else:
            # Redis sigle node cluster
            # Because all Redis clusters are single nodes, we'll merge the
            # info from the cluster with info about the node
            dest = cluster['CacheNodes'][0]['Endpoint']['Address']
            is_redis = True

        if not dest:
            # Skip clusters we cannot address (e.g. private VPC subnet)
            return

        # Add to index
        self.index[dest] = [region, cluster['CacheClusterId']]

        # Inventory: Group by instance ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[cluster['CacheClusterId']] = [dest]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', cluster['CacheClusterId'])

        # Inventory: Group by region
        if self.group_by_region and not is_redis:
            self.push(self.inventory, region, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)

        # Inventory: Group by availability zone
        if self.group_by_availability_zone and not is_redis:
            self.push(self.inventory, cluster['PreferredAvailabilityZone'], dest)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, cluster['PreferredAvailabilityZone'])
                self.push_group(self.inventory, 'zones', cluster['PreferredAvailabilityZone'])

        # Inventory: Group by node type
        if self.group_by_instance_type and not is_redis:
            type_name = self.to_safe('type_' + cluster['CacheNodeType'])
            self.push(self.inventory, type_name, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)

        # Inventory: Group by VPC (information not available in the current
        # AWS API version for ElastiCache)

        # Inventory: Group by security group
        if self.group_by_security_group and not is_redis:

            # Check for the existence of the 'SecurityGroups' key and also if
            # this key has some value. When the cluster is not placed in a SG
            # the query can return None here and cause an error.
            if 'SecurityGroups' in cluster and cluster['SecurityGroups'] is not None:
                for security_group in cluster['SecurityGroups']:
                    key = self.to_safe("security_group_" + security_group['SecurityGroupId'])
                    self.push(self.inventory, key, dest)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)

        # Inventory: Group by engine
        if self.group_by_elasticache_engine and not is_redis:
            self.push(self.inventory, self.to_safe("elasticache_" + cluster['Engine']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_engines', self.to_safe(cluster['Engine']))

        # Inventory: Group by parameter group
        if self.group_by_elasticache_parameter_group:
            self.push(self.inventory, self.to_safe("elasticache_parameter_group_" + cluster['CacheParameterGroup']['CacheParameterGroupName']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_parameter_groups', self.to_safe(cluster['CacheParameterGroup']['CacheParameterGroupName']))

        # Inventory: Group by replication group
        if self.group_by_elasticache_replication_group and 'ReplicationGroupId' in cluster and cluster['ReplicationGroupId']:
            self.push(self.inventory, self.to_safe("elasticache_replication_group_" + cluster['ReplicationGroupId']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_replication_groups', self.to_safe(cluster['ReplicationGroupId']))

        # Global Tag: all ElastiCache clusters
        self.push(self.inventory, 'elasticache_clusters', cluster['CacheClusterId'])

        host_info = self.get_host_info_dict_from_describe_dict(cluster)

        self.inventory["_meta"]["hostvars"][dest] = host_info

        # Add the nodes
        for node in cluster['CacheNodes']:
            self.add_elasticache_node(node, cluster, region)

    def add_elasticache_node(self, node, cluster, region):
        ''' Adds an ElastiCache node to the inventory and index, as long as
        it is addressable '''

        # Only want available nodes unless all_elasticache_nodes is True
        if not self.all_elasticache_nodes and node['CacheNodeStatus'] != 'available':
            return

        # Select the best destination address
        dest = node['Endpoint']['Address']

        if not dest:
            # Skip nodes we cannot address (e.g. private VPC subnet)
            return

        node_id = self.to_safe(cluster['CacheClusterId'] + '_' + node['CacheNodeId'])

        # Add to index
        self.index[dest] = [region, node_id]

        # Inventory: Group by node ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[node_id] = [dest]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', node_id)

        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)

        # Inventory: Group by availability zone
        if self.group_by_availability_zone:
            self.push(self.inventory, cluster['PreferredAvailabilityZone'], dest)
            if self.nested_groups:
                if self.group_by_region:
                    self.push_group(self.inventory, region, cluster['PreferredAvailabilityZone'])
                self.push_group(self.inventory, 'zones', cluster['PreferredAvailabilityZone'])

        # Inventory: Group by node type
        if self.group_by_instance_type:
            type_name = self.to_safe('type_' + cluster['CacheNodeType'])
            self.push(self.inventory, type_name, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'types', type_name)

        # Inventory: Group by VPC (information not available in the current
        # AWS API version for ElastiCache)

        # Inventory: Group by security group
        if self.group_by_security_group:

            # Check for the existence of the 'SecurityGroups' key and also if
            # this key has some value. When the cluster is not placed in a SG
            # the query can return None here and cause an error.
            if 'SecurityGroups' in cluster and cluster['SecurityGroups'] is not None:
                for security_group in cluster['SecurityGroups']:
                    key = self.to_safe("security_group_" + security_group['SecurityGroupId'])
                    self.push(self.inventory, key, dest)
                    if self.nested_groups:
                        self.push_group(self.inventory, 'security_groups', key)

        # Inventory: Group by engine
        if self.group_by_elasticache_engine:
            self.push(self.inventory, self.to_safe("elasticache_" + cluster['Engine']), dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_engines', self.to_safe("elasticache_" + cluster['Engine']))

        # Inventory: Group by parameter group (done at cluster level)

        # Inventory: Group by replication group (done at cluster level)

        # Inventory: Group by ElastiCache Cluster
        if self.group_by_elasticache_cluster:
            self.push(self.inventory, self.to_safe("elasticache_cluster_" + cluster['CacheClusterId']), dest)

        # Global Tag: all ElastiCache nodes
        self.push(self.inventory, 'elasticache_nodes', dest)

        host_info = self.get_host_info_dict_from_describe_dict(node)

        if dest in self.inventory["_meta"]["hostvars"]:
            self.inventory["_meta"]["hostvars"][dest].update(host_info)
        else:
            self.inventory["_meta"]["hostvars"][dest] = host_info

    def add_elasticache_replication_group(self, replication_group, region):
        ''' Adds an ElastiCache replication group to the inventory and index '''

        # Only want available clusters unless all_elasticache_replication_groups is True
        if not self.all_elasticache_replication_groups and replication_group['Status'] != 'available':
            return

        # Skip clusters we cannot address (e.g. private VPC subnet or clustered redis)
        if replication_group['NodeGroups'][0]['PrimaryEndpoint'] is None or \
           replication_group['NodeGroups'][0]['PrimaryEndpoint']['Address'] is None:
            return

        # Select the best destination address (PrimaryEndpoint)
        dest = replication_group['NodeGroups'][0]['PrimaryEndpoint']['Address']

        # Add to index
        self.index[dest] = [region, replication_group['ReplicationGroupId']]

        # Inventory: Group by ID (always a group of 1)
        if self.group_by_instance_id:
            self.inventory[replication_group['ReplicationGroupId']] = [dest]
            if self.nested_groups:
                self.push_group(self.inventory, 'instances', replication_group['ReplicationGroupId'])

        # Inventory: Group by region
        if self.group_by_region:
            self.push(self.inventory, region, dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'regions', region)

        # Inventory: Group by availability zone (doesn't apply to replication groups)

        # Inventory: Group by node type (doesn't apply to replication groups)

        # Inventory: Group by VPC (information not available in the current
        # AWS API version for replication groups

        # Inventory: Group by security group (doesn't apply to replication groups)
        # Check this value in cluster level

        # Inventory: Group by engine (replication groups are always Redis)
        if self.group_by_elasticache_engine:
            self.push(self.inventory, 'elasticache_redis', dest)
            if self.nested_groups:
                self.push_group(self.inventory, 'elasticache_engines', 'redis')

        # Global Tag: all ElastiCache clusters
        self.push(self.inventory, 'elasticache_replication_groups', replication_group['ReplicationGroupId'])

        host_info = self.get_host_info_dict_from_describe_dict(replication_group)

        self.inventory["_meta"]["hostvars"][dest] = host_info

    def get_route53_records(self):
        ''' Get and store the map of resource records to domain names that
        point to them. '''

        if self.boto_profile:
            r53_conn = route53.Route53Connection(profile_name=self.boto_profile)
        else:
            r53_conn = route53.Route53Connection()
        all_zones = r53_conn.get_zones()

        route53_zones = [ zone for zone in all_zones if zone.name[:-1]
                          not in self.route53_excluded_zones ]

        self.route53_records = {}

        for zone in route53_zones:
            rrsets = r53_conn.get_all_rrsets(zone.id)

            for record_set in rrsets:
                record_name = record_set.name

                if record_name.endswith('.'):
                    record_name = record_name[:-1]

                for resource in record_set.resource_records:
                    self.route53_records.setdefault(resource, set())
                    self.route53_records[resource].add(record_name)


    def get_instance_route53_names(self, instance):
        ''' Check if an instance is referenced in the records we have from
        Route53. If it is, return the list of domain names pointing to said
        instance. If nothing points to it, return an empty list. '''

        instance_attributes = [ 'public_dns_name', 'private_dns_name',
                                'ip_address', 'private_ip_address' ]

        name_list = set()

        for attrib in instance_attributes:
            try:
                value = getattr(instance, attrib)
            except AttributeError:
                continue

            if value in self.route53_records:
                name_list.update(self.route53_records[value])

        return list(name_list)

    def get_host_info_dict_from_instance(self, instance):
        instance_vars = {}
        for key in vars(instance):
            value = getattr(instance, key)
            key = self.to_safe('ec2_' + key)

            # Handle complex types
            # state/previous_state changed to properties in boto in https://github.com/boto/boto/commit/a23c379837f698212252720d2af8dec0325c9518
            if key == 'ec2__state':
                instance_vars['ec2_state'] = instance.state or ''
                instance_vars['ec2_state_code'] = instance.state_code
            elif key == 'ec2__previous_state':
                instance_vars['ec2_previous_state'] = instance.previous_state or ''
                instance_vars['ec2_previous_state_code'] = instance.previous_state_code
            elif type(value) in [int, bool]:
                instance_vars[key] = value
            elif isinstance(value, six.string_types):
                instance_vars[key] = value.strip()
            elif value is None:
                instance_vars[key] = ''
            elif key == 'ec2_region':
                instance_vars[key] = value.name
            elif key == 'ec2__placement':
                instance_vars['ec2_placement'] = value.zone
            elif key == 'ec2_tags':
                for k, v in value.items():
                    if self.expand_csv_tags and ',' in v:
                        v = list(map(lambda x: x.strip(), v.split(',')))
                    key = self.to_safe('ec2_tag_' + k)
                    instance_vars[key] = v
            elif key == 'ec2_groups':
                group_ids = []
                group_names = []
                for group in value:
                    group_ids.append(group.id)
                    group_names.append(group.name)
                instance_vars["ec2_security_group_ids"] = ','.join([str(i) for i in group_ids])
                instance_vars["ec2_security_group_names"] = ','.join([str(i) for i in group_names])
            elif key == 'ec2_block_device_mapping':
                instance_vars["ec2_block_devices"] = {}
                for k, v in value.items():
                    instance_vars["ec2_block_devices"][ os.path.basename(k) ] = v.volume_id
            else:
                pass
                # TODO Product codes if someone finds them useful
                #print key
                #print type(value)
                #print value

        instance_vars[self.to_safe('ec2_account_id')] = self.aws_account_id

        return instance_vars

    def get_host_info_dict_from_describe_dict(self, describe_dict):
        ''' Parses the dictionary returned by the API call into a flat list
            of parameters. This method should be used only when 'describe' is
            used directly because Boto doesn't provide specific classes. '''

        # I really don't agree with prefixing everything with 'ec2'
        # because EC2, RDS and ElastiCache are different services.
        # I'm just following the pattern used until now to not break any
        # compatibility.

        host_info = {}
        for key in describe_dict:
            value = describe_dict[key]
            key = self.to_safe('ec2_' + self.uncammelize(key))

            # Handle complex types

            # Target: Memcached Cache Clusters
            if key == 'ec2_configuration_endpoint' and value:
                host_info['ec2_configuration_endpoint_address'] = value['Address']
                host_info['ec2_configuration_endpoint_port'] = value['Port']

            # Target: Cache Nodes and Redis Cache Clusters (single node)
            if key == 'ec2_endpoint' and value:
                host_info['ec2_endpoint_address'] = value['Address']
                host_info['ec2_endpoint_port'] = value['Port']

            # Target: Redis Replication Groups
            if key == 'ec2_node_groups' and value:
                host_info['ec2_endpoint_address'] = value[0]['PrimaryEndpoint']['Address']
                host_info['ec2_endpoint_port'] = value[0]['PrimaryEndpoint']['Port']
                replica_count = 0
                for node in value[0]['NodeGroupMembers']:
                    if node['CurrentRole'] == 'primary':
                        host_info['ec2_primary_cluster_address'] = node['ReadEndpoint']['Address']
                        host_info['ec2_primary_cluster_port'] = node['ReadEndpoint']['Port']
                        host_info['ec2_primary_cluster_id'] = node['CacheClusterId']
                    elif node['CurrentRole'] == 'replica':
                        host_info['ec2_replica_cluster_address_'+ str(replica_count)] = node['ReadEndpoint']['Address']
                        host_info['ec2_replica_cluster_port_'+ str(replica_count)] = node['ReadEndpoint']['Port']
                        host_info['ec2_replica_cluster_id_'+ str(replica_count)] = node['CacheClusterId']
                        replica_count += 1

            # Target: Redis Replication Groups
            if key == 'ec2_member_clusters' and value:
                host_info['ec2_member_clusters'] = ','.join([str(i) for i in value])

            # Target: All Cache Clusters
            elif key == 'ec2_cache_parameter_group':
                host_info["ec2_cache_node_ids_to_reboot"] = ','.join([str(i) for i in value['CacheNodeIdsToReboot']])
                host_info['ec2_cache_parameter_group_name'] = value['CacheParameterGroupName']
                host_info['ec2_cache_parameter_apply_status'] = value['ParameterApplyStatus']

            # Target: Almost everything
            elif key == 'ec2_security_groups':

                # Skip if SecurityGroups is None
                # (it is possible to have the key defined but no value in it).
                if value is not None:
                    sg_ids = []
                    for sg in value:
                        sg_ids.append(sg['SecurityGroupId'])
                    host_info["ec2_security_group_ids"] = ','.join([str(i) for i in sg_ids])

            # Target: Everything
            # Preserve booleans and integers
            elif type(value) in [int, bool]:
                host_info[key] = value

            # Target: Everything
            # Sanitize string values
            elif isinstance(value, six.string_types):
                host_info[key] = value.strip()

            # Target: Everything
            # Replace None by an empty string
            elif value is None:
                host_info[key] = ''

            else:
                # Remove non-processed complex types
                pass

        return host_info

    def get_host_info(self):
        ''' Get variables about a specific host '''

        if len(self.index) == 0:
            # Need to load index from cache
            self.load_index_from_cache()

        if not self.args.host in self.index:
            # try updating the cache
            self.do_api_calls_update_cache()
            if not self.args.host in self.index:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        (region, instance_id) = self.index[self.args.host]

        instance = self.get_instance(region, instance_id)
        return self.json_format_dict(self.get_host_info_dict_from_instance(instance), True)

    def push(self, my_dict, key, element):
        ''' Push an element onto an array that may not have been defined in
        the dict '''
        group_info = my_dict.setdefault(key, [])
        if isinstance(group_info, dict):
            host_list = group_info.setdefault('hosts', [])
            host_list.append(element)
        else:
            group_info.append(element)

    def push_group(self, my_dict, key, element):
        ''' Push a group as a child of another group. '''
        parent_group = my_dict.setdefault(key, {})
        if not isinstance(parent_group, dict):
            parent_group = my_dict[key] = {'hosts': parent_group}
        child_groups = parent_group.setdefault('children', [])
        if element not in child_groups:
            child_groups.append(element)

    def get_inventory_from_cache(self):
        ''' Reads the inventory from the cache file and returns it as a JSON
        object '''

        with open(self.cache_path_cache, 'r') as f:
            json_inventory = f.read()
            return json_inventory

    def load_index_from_cache(self):
        ''' Reads the index from the cache file sets self.index '''

        with open(self.cache_path_index, 'rb') as f:
            self.index = json.load(f)

    def write_to_cache(self, data, filename):
        ''' Writes data in JSON format to a file '''

        json_data = self.json_format_dict(data, True)
        with open(filename, 'w') as f:
            f.write(json_data)

    def uncammelize(self, key):
        temp = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', key)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', temp).lower()

    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used as Ansible groups '''
        regex = "[^A-Za-z0-9\_"
        if not self.replace_dash_in_groups:
            regex += "\-"
        return re.sub(regex + "]", "_", word)

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


if __name__ == '__main__':
    # Run the script
    Ec2Inventory()
