# Copyright (c) 2013 eBay Inc.
# Copyright (c) OpenStack LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
QoS Specs interface.
"""

from cinderclient import base


class QoSSpecs(base.Resource):
    """QoS specs entity represents quality-of-service parameters/requirements.

    A QoS specs is a set of parameters or requirements for quality-of-service
    purpose, which can be associated with volume types (for now).  In future,
    QoS specs may be extended to be associated other entities, such as single
    volume.
    """
    def __repr__(self):
        return "<QoSSpecs: %s>" % self.name

    def delete(self):
        return self.manager.delete(self)


class QoSSpecsManager(base.ManagerWithFind):
    """
    Manage :class:`QoSSpecs` resources.
    """
    resource_class = QoSSpecs

    def list(self):
        """Get a list of all qos specs.

        :rtype: list of :class:`QoSSpecs`.
        """
        return self._list("/qos-specs", "qos_specs")

    def get(self, qos_specs):
        """Get a specific qos specs.

        :param qos_specs: The ID of the :class:`QoSSpecs` to get.
        :rtype: :class:`QoSSpecs`
        """
        return self._get("/qos-specs/%s" % base.getid(qos_specs), "qos_specs")

    def delete(self, qos_specs, force=False):
        """Delete a specific qos specs.

        :param qos_specs: The ID of the :class:`QoSSpecs` to be removed.
        :param force: Flag that indicates whether to delete target qos specs
                      if it was in-use.
        """
        self._delete("/qos-specs/%s?force=%s" %
                     (base.getid(qos_specs), force))

    def create(self, name, specs):
        """Create a qos specs.

        :param name: Descriptive name of the qos specs, must be unique
        :param specs: A dict of key/value pairs to be set
        :rtype: :class:`QoSSpecs`
        """

        body = {
            "qos_specs": {
                "name": name,
            }
        }

        body["qos_specs"].update(specs)
        return self._create("/qos-specs", body, "qos_specs")

    def set_keys(self, qos_specs, specs):
        """Update a qos specs with new specifications.

        :param qos_specs: The ID of qos specs
        :param specs: A dict of key/value pairs to be set
        :rtype: :class:`QoSSpecs`
        """

        body = {
            "qos_specs": {}
        }

        body["qos_specs"].update(specs)
        return self._update("/qos-specs/%s" % qos_specs, body)

    def unset_keys(self, qos_specs, specs):
        """Update a qos specs with new specifications.

        :param qos_specs: The ID of qos specs
        :param specs: A list of key to be unset
        :rtype: :class:`QoSSpecs`
        """

        body = {'keys': specs}

        return self._update("/qos-specs/%s/delete_keys" % qos_specs,
                            body)

    def get_associations(self, qos_specs):
        """Get associated entities of a qos specs.

        :param qos_specs: The id of the :class: `QoSSpecs`
        :return: a list of entities that associated with specific qos specs.
        """
        return self._list("/qos-specs/%s/associations" % base.getid(qos_specs),
                          "qos_associations")

    def associate(self, qos_specs, vol_type_id):
        """Associate a volume type with specific qos specs.

        :param qos_specs: The qos specs to be associated with
        :param vol_type_id: The volume type id to be associated with
        """
        self.api.client.get("/qos-specs/%s/associate?vol_type_id=%s" %
                            (base.getid(qos_specs), vol_type_id))

    def disassociate(self, qos_specs, vol_type_id):
        """Disassociate qos specs from volume type.

        :param qos_specs: The qos specs to be associated with
        :param vol_type_id: The volume type id to be associated with
        """
        self.api.client.get("/qos-specs/%s/disassociate?vol_type_id=%s" %
                            (base.getid(qos_specs), vol_type_id))

    def disassociate_all(self, qos_specs):
        """Disassociate all entities from specific qos specs.

        :param qos_specs: The qos specs to be associated with
        """
        self.api.client.get("/qos-specs/%s/disassociate_all" %
                            base.getid(qos_specs))
