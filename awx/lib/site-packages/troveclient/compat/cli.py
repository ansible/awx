#!/usr/bin/env python

#    Copyright 2011 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Trove Command line tool
"""

import os
import sys


# If ../trove/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
possible_topdir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
                                                os.pardir,
                                                os.pardir))
if os.path.exists(os.path.join(possible_topdir, 'troveclient',
                               '__init__.py')):
    sys.path.insert(0, possible_topdir)

from troveclient.compat import common


class InstanceCommands(common.AuthedCommandsBase):
    """Commands to perform various instance operations and actions."""

    params = [
        'flavor',
        'id',
        'limit',
        'marker',
        'name',
        'size',
        'backup',
        'availability_zone',
        'configuration_id',
    ]

    def _get_configuration_ref(self):
        configuration_ref = None
        if self.configuration_id is not None:
            if self.configuration_id == "":
                configuration_ref = self.configuration_id
            else:
                configuration_ref = "/".join(
                    [
                        self.dbaas.client.service_url,
                        self.configuration_id,
                    ]
                )
        return configuration_ref

    def create(self):
        """Create a new instance."""
        self._require('name', 'flavor')
        volume = None
        if self.size:
            volume = {"size": self.size}
        restorePoint = None
        if self.backup:
            restorePoint = {"backupRef": self.backup}
        self._pretty_print(self.dbaas.instances.create, self.name,
                           self.flavor, volume, restorePoint=restorePoint,
                           availability_zone=self.availability_zone,
                           configuration=self._get_configuration_ref())

    # TODO(pdmars): is this actually what this should be named?
    def modify(self):
        """Modify an instance."""
        self._require('id')
        self._pretty_print(self.dbaas.instances.modify, self.id,
                           configuration=self._get_configuration_ref())

    def delete(self):
        """Delete the specified instance."""
        self._require('id')
        print(self.dbaas.instances.delete(self.id))

    def get(self):
        """Get details for the specified instance."""
        self._require('id')
        self._pretty_print(self.dbaas.instances.get, self.id)

    def backups(self):
        """Get a list of backups for the specified instance."""
        self._require('id')
        self._pretty_list(self.dbaas.instances.backups, self.id)

    def list(self):
        """List all instances for account."""
        # limit and marker are not required.
        limit = self.limit or None
        if limit:
            limit = int(limit, 10)
        self._pretty_paged(self.dbaas.instances.list)

    def resize_volume(self):
        """Resize an instance volume."""
        self._require('id', 'size')
        self._pretty_print(self.dbaas.instances.resize_volume, self.id,
                           self.size)

    def resize_instance(self):
        """Resize an instance flavor"""
        self._require('id', 'flavor')
        self._pretty_print(self.dbaas.instances.resize_instance, self.id,
                           self.flavor)

    def restart(self):
        """Restart the database."""
        self._require('id')
        self._pretty_print(self.dbaas.instances.restart, self.id)

    def configuration(self):
        """Get configuration for the specified instance."""
        self._require('id')
        self._pretty_print(self.dbaas.instances.configuration, self.id)


class FlavorsCommands(common.AuthedCommandsBase):
    """Command for listing Flavors."""

    params = []

    def list(self):
        """List the available flavors."""
        self._pretty_list(self.dbaas.flavors.list)


class DatabaseCommands(common.AuthedCommandsBase):
    """Database CRUD operations on an instance."""

    params = [
        'name',
        'id',
        'limit',
        'marker',
    ]

    def create(self):
        """Create a database."""
        self._require('id', 'name')
        databases = [{'name': self.name}]
        print(self.dbaas.databases.create(self.id, databases))

    def delete(self):
        """Delete a database."""
        self._require('id', 'name')
        print(self.dbaas.databases.delete(self.id, self.name))

    def list(self):
        """List the databases."""
        self._require('id')
        self._pretty_paged(self.dbaas.databases.list, self.id)


class UserCommands(common.AuthedCommandsBase):
    """User CRUD operations on an instance."""
    params = [
        'id',
        'database',
        'databases',
        'hostname',
        'name',
        'password',
        'new_name',
        'new_host',
        'new_password',
    ]

    def create(self):
        """Create a user in instance, with access to one or more databases."""
        self._require('id', 'name', 'password', 'databases')
        self._make_list('databases')
        databases = [{'name': dbname} for dbname in self.databases]
        users = [{'name': self.name, 'password': self.password,
                  'databases': databases}]
        if self.hostname:
            users[0]['host'] = self.hostname
        self.dbaas.users.create(self.id, users)

    def delete(self):
        """Delete the specified user"""
        self._require('id', 'name')
        self.dbaas.users.delete(self.id, self.name, self.hostname)

    def get(self):
        """Get a single user."""
        self._require('id', 'name')
        self._pretty_print(self.dbaas.users.get, self.id,
                           self.name, self.hostname)

    def update_attributes(self):
        """Update attributes of a single user."""
        self._require('id', 'name')
        self._require_at_least_one_of('new_name', 'new_host', 'new_password')
        user_new = {}
        if self.new_name:
            user_new['name'] = self.new_name
        if self.new_host:
            user_new['host'] = self.new_host
        if self.new_password:
            user_new['password'] = self.new_password
        self.dbaas.users.update_attributes(self.id, self.name, user_new,
                                           self.hostname)

    def list(self):
        """List all the users for an instance."""
        self._require('id')
        self._pretty_paged(self.dbaas.users.list, self.id)

    def access(self):
        """Show all databases the user has access to."""
        self._require('id', 'name')
        self._pretty_list(self.dbaas.users.list_access, self.id,
                          self.name, self.hostname)

    def grant(self):
        """Allow an existing user permissions to access one or more
        databases.
        """
        self._require('id', 'name', 'databases')
        self._make_list('databases')
        self.dbaas.users.grant(self.id, self.name, self.databases,
                               self.hostname)

    def revoke(self):
        """Revoke from an existing user access permissions to a database."""
        self._require('id', 'name', 'database')
        self.dbaas.users.revoke(self.id, self.name, self.database,
                                self.hostname)

    def change_password(self):
        """Change the password of a single user."""
        self._require('id', 'name', 'password')
        users = [{'name': self.name,
                  'host': self.hostname,
                  'password': self.password}]
        self.dbaas.users.change_passwords(self.id, users)


class RootCommands(common.AuthedCommandsBase):
    """Root user related operations on an instance."""

    params = [
        'id',
    ]

    def create(self):
        """Enable the instance's root user."""
        self._require('id')
        try:
            user, password = self.dbaas.root.create(self.id)
            print("User:\t\t%s\nPassword:\t%s" % (user, password))
        except Exception:
            print(sys.exc_info()[1])

    def enabled(self):
        """Check the instance for root access."""
        self._require('id')
        self._pretty_print(self.dbaas.root.is_root_enabled, self.id)


class VersionCommands(common.AuthedCommandsBase):
    """List available versions."""

    params = [
        'url',
    ]

    def list(self):
        """List all the supported versions."""
        self._require('url')
        self._pretty_list(self.dbaas.versions.index, self.url)


class LimitsCommands(common.AuthedCommandsBase):
    """Show the rate limits and absolute limits."""

    def list(self):
        """List the rate limits and absolute limits."""
        self._pretty_list(self.dbaas.limits.list)


class BackupsCommands(common.AuthedCommandsBase):
    """Command to manage and show backups."""
    params = ['name', 'instance', 'description']

    def get(self):
        """Get details for the specified backup."""
        self._require('id')
        self._pretty_print(self.dbaas.backups.get, self.id)

    def list(self):
        """List backups."""
        self._pretty_list(self.dbaas.backups.list)

    def create(self):
        """Create a new backup."""
        self._require('name', 'instance')
        self._pretty_print(self.dbaas.backups.create, self.name,
                           self.instance, self.description)

    def delete(self):
        """Delete a backup."""
        self._require('id')
        self._pretty_print(self.dbaas.backups.delete, self.id)


class DatastoreConfigurationParameters(common.AuthedCommandsBase):
    """Command to show configuration parameters for a datastore."""
    params = ['datastore', 'parameter']

    def parameters(self):
        """List parameters that can be set."""
        self._require('datastore')
        self._pretty_print(self.dbaas.configuration_parameters.parameters,
                           self.datastore)

    def get_parameter(self):
        """List parameters that can be set."""
        self._require('datastore', 'parameter')
        self._pretty_print(self.dbaas.configuration_parameters.get_parameter,
                           self.datastore, self.parameter)


class ConfigurationsCommands(common.AuthedCommandsBase):
    """Command to manage and show configurations."""
    params = ['name', 'instances', 'values', 'description', 'parameter']

    def get(self):
        """Get details for the specified configuration."""
        self._require('id')
        self._pretty_print(self.dbaas.configurations.get, self.id)

    def list_instances(self):
        """Get details for the specified configuration."""
        self._require('id')
        self._pretty_list(self.dbaas.configurations.instances, self.id)

    def list(self):
        """List configurations."""
        self._pretty_list(self.dbaas.configurations.list)

    def create(self):
        """Create a new configuration."""
        self._require('name', 'values')
        self._pretty_print(self.dbaas.configurations.create, self.name,
                           self.values, self.description)

    def update(self):
        """Update an existing configuration."""
        self._require('id', 'values')
        self._pretty_print(self.dbaas.configurations.update, self.id,
                           self.values, self.name, self.description)

    def edit(self):
        """Edit an existing configuration values."""
        self._require('id', 'values')
        self._pretty_print(self.dbaas.configurations.edit, self.id,
                           self.values)

    def delete(self):
        """Delete a configuration."""
        self._require('id')
        self._pretty_print(self.dbaas.configurations.delete, self.id)


class SecurityGroupCommands(common.AuthedCommandsBase):
    """Commands to list and show Security Groups For an Instance and
    create and delete security group rules for them.
    """
    params = [
        'id',
        'secgroup_id',
        'protocol',
        'from_port',
        'to_port',
        'cidr'
    ]

    def get(self):
        """Get a security group associated with an instance."""
        self._require('id')
        self._pretty_print(self.dbaas.security_groups.get, self.id)

    def list(self):
        """List all the Security Groups and the rules."""
        self._pretty_paged(self.dbaas.security_groups.list)

    def add_rule(self):
        """Add a security group rule."""
        self._require('secgroup_id', 'protocol',
                      'from_port', 'to_port', 'cidr')
        self.dbaas.security_group_rules.create(self.secgroup_id, self.protocol,
                                               self.from_port, self.to_port,
                                               self.cidr)

    def delete_rule(self):
        """Delete a security group rule."""
        self._require('id')
        self.dbaas.security_group_rules.delete(self.id)


class MetadataCommands(common.AuthedCommandsBase):
    """Commands to create/update/replace/delete/show metadata for an instance
    """
    params = [
        'instance_id',
        'metadata'
    ]

    def show(self):
        """Show instance metadata."""
        self._require('instance_id')
        self._pretty_print(self.dbaas.metadata.show(self.instance_id))


COMMANDS = {
    'auth': common.Auth,
    'instance': InstanceCommands,
    'flavor': FlavorsCommands,
    'database': DatabaseCommands,
    'limit': LimitsCommands,
    'backup': BackupsCommands,
    'configuration': ConfigurationsCommands,
    'user': UserCommands,
    'root': RootCommands,
    'version': VersionCommands,
    'secgroup': SecurityGroupCommands,
    'metadata': MetadataCommands,
}


def main():
    # Parse arguments
    load_file = True
    for index, arg in enumerate(sys.argv):
        if (arg == "auth" and len(sys.argv) > (index + 1)
                and sys.argv[index + 1] == "login"):
            load_file = False

    oparser = common.CliOptions.create_optparser(load_file)
    for k, v in COMMANDS.items():
        v._prepare_parser(oparser)
    (options, args) = oparser.parse_args()

    if not args:
        common.print_commands(COMMANDS)

    if options.verbose:
        os.environ['RDC_PP'] = "True"
        os.environ['REDDWARFCLIENT_DEBUG'] = "True"

    # Pop the command and check if it's in the known commands
    cmd = args.pop(0)
    if cmd in COMMANDS:
        fn = COMMANDS.get(cmd)
        command_object = None
        try:
            command_object = fn(oparser)
        except Exception as ex:
            if options.debug:
                raise
            print(ex)

        # Get a list of supported actions for the command
        actions = common.methods_of(command_object)

        if len(args) < 1:
            common.print_actions(cmd, actions)

        # Check for a valid action and perform that action
        action = args.pop(0)
        if action in actions:
            if not options.debug:
                try:
                    getattr(command_object, action)()
                except Exception as ex:
                    if options.debug:
                        raise
                    print(ex)
            else:
                getattr(command_object, action)()
        else:
            common.print_actions(cmd, actions)
    else:
        common.print_commands(COMMANDS)


if __name__ == '__main__':
    main()
