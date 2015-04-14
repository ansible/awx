# Copyright (c) 2014 OpenStack, LLC.
# All Rights Reserved.
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


import json
from troveclient import base
from troveclient import common


class Configuration(base.Resource):
    """Configuration is a resource used to hold configuration information."""
    def __repr__(self):
        return "<Configuration: %s>" % self.name


class Configurations(base.ManagerWithFind):
    """Manage :class:`Configurations` information."""

    resource_class = Configuration

    def get(self, configuration):
        """Get a specific configuration.

        :rtype: :class:`Configurations`
        """
        return self._get("/configurations/%s" % base.getid(configuration),
                         "configuration")

    def instances(self, configuration, limit=None, marker=None):
        """Get a list of instances on a configuration.

        :rtype: :class:`Configurations`
        """
        return self._list("/configurations/%s/instances" %
                          base.getid(configuration),
                          "instances", limit, marker)

    def list(self, limit=None, marker=None):
        """Get a list of all configurations.

        :rtype: list of :class:`Configurations`.
        """
        return self._list("/configurations", "configurations", limit, marker)

    def create(self, name, values, description=None, datastore=None,
               datastore_version=None):
        """Create a new configuration."""
        body = {
            "configuration": {
                "name": name,
                "values": json.loads(values)
            }
        }
        datastore_obj = {}
        if datastore:
            datastore_obj["type"] = datastore
        if datastore_version:
            datastore_obj["version"] = datastore_version
        if datastore_obj:
            body["configuration"]["datastore"] = datastore_obj
        if description:
            body['configuration']['description'] = description
        return self._create("/configurations", body, "configuration")

    def update(self, configuration_id, values, name=None, description=None):
        """Update an existing configuration."""
        body = {
            "configuration": {
                "values": json.loads(values)
            }
        }
        if name:
            body['configuration']['name'] = name
        if description:
            body['configuration']['description'] = description
        url = "/configurations/%s" % configuration_id
        resp, body = self.api.client.put(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def edit(self, configuration_id, values):
        """Update an existing configuration."""
        body = {
            "configuration": {
                "values": json.loads(values)
            }
        }
        url = "/configurations/%s" % configuration_id
        resp, body = self.api.client.patch(url, body=body)
        common.check_for_exceptions(resp, body, url)

    def delete(self, configuration_id):
        """Delete the specified configuration.

        :param configuration_id: The configuration id to delete
        """
        url = "/configurations/%s" % configuration_id
        resp, body = self.api.client.delete(url)
        common.check_for_exceptions(resp, body, url)


class ConfigurationParameter(base.Resource):
    """Configuration Parameter."""
    def __repr__(self):
        return "<ConfigurationParameter: %s>" % self.__dict__


class ConfigurationParameters(base.ManagerWithFind):
    """Manage :class:`ConfigurationParameters` information."""

    resource_class = ConfigurationParameter

    def parameters(self, datastore, version):
        """Get a list of valid parameters that can be changed."""
        return self._list("/datastores/%s/versions/%s/parameters" %
                          (datastore, version), "configuration-parameters")

    def get_parameter(self, datastore, version, key):
        """Get a list of valid parameters that can be changed."""
        return self._get("/datastores/%s/versions/%s/parameters/%s" %
                         (datastore, version, key))

    def parameters_by_version(self, version):
        """Get a list of valid parameters that can be changed."""
        return self._list("/datastores/versions/%s/parameters" % version,
                          "configuration-parameters")

    def get_parameter_by_version(self, version, key):
        """Get a list of valid parameters that can be changed."""
        return self._get("/datastores/versions/%s/parameters/%s" %
                         (version, key))

    # Appease the abc gods
    def list(self):
        pass
