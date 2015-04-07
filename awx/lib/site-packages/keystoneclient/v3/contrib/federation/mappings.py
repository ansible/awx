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

from keystoneclient import base
from keystoneclient import utils


class Mapping(base.Resource):
    """An object representing mapping container

    Attributes:
        * id: user defined unique string identifying mapping.

    """
    pass


class MappingManager(base.CrudManager):
    """Manager class for manipulating federation mappings."""

    resource_class = Mapping
    collection_key = 'mappings'
    key = 'mapping'
    base_url = 'OS-FEDERATION'

    def _build_url_and_put(self, **kwargs):
        url = self.build_url(dict_args_in_out=kwargs)
        body = {self.key: kwargs}
        return self._update(url, body=body,
                            response_key=self.key,
                            method='PUT')

    @utils.positional.method(0)
    def create(self, mapping_id, **kwargs):
        """Create federation mapping.

        Utilize Identity API operation:
        PUT /OS-FEDERATION/mappings/$mapping_id

        :param mapping_id: user defined string identifier of the federation
            mapping.
        :param rules: a list of mapping rules.

        Example of the ``rules`` parameter::

             [
                 {
                     "local": [
                         {
                             "group": {
                                 "id": "0cd5e9"
                             }
                         }
                     ],
                     "remote": [
                         {
                             "type": "orgPersonType",
                             "not_any_of": [
                                 "Contractor",
                                 "Guest"
                             ]
                         }
                     ]
                 }
             ]

        """
        return self._build_url_and_put(
            mapping_id=mapping_id, **kwargs)

    def get(self, mapping):
        """Fetch federation mapping identified by mapping id.

        Utilize Identity API operation:
        GET /OS-FEDERATION/mappings/$mapping_id

        :param mapping: a Mapping type object with mapping id
            stored inside.

        """
        return super(MappingManager, self).get(
            mapping_id=base.getid(mapping))

    def list(self, **kwargs):
        """List all federation mappings.

        Utilize Identity API operation:
        GET /OS-FEDERATION/mappings/$mapping_id

        """
        return super(MappingManager, self).list(**kwargs)

    def update(self, mapping, **kwargs):
        """Update federation mapping identified by mapping id.

        Utilize Identity API operation:
        PATCH /OS-FEDERATION/mappings/$mapping_id

        :param mapping: a Mapping type object with mapping id
            stored inside.
        :param rules: a list of mapping rules.

        Example of the ``rules`` parameter::


             [
                 {
                     "local": [
                         {
                             "group": {
                                 "id": "0cd5e9"
                             }
                         }
                     ],
                     "remote": [
                         {
                             "type": "orgPersonType",
                             "not_any_of": [
                                 "Contractor",
                                 "Guest"
                             ]
                         }
                     ]
                 }
             ]

        """
        return super(MappingManager, self).update(
            mapping_id=base.getid(mapping), **kwargs)

    def delete(self, mapping):
        """Delete federation mapping identified by mapping id.

        Utilize Identity API operation:
        DELETE /OS-FEDERATION/mappings/$mapping_id

        :param mapping: a Mapping type object with mapping id
            stored inside.

        """
        return super(MappingManager, self).delete(
            mapping_id=base.getid(mapping))
