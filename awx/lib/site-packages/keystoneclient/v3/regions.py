# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from keystoneclient import base


class Region(base.Resource):
    """Represents a Catalog region.

    Attributes:
        * id: a string that identifies the region.
        * description: a string that describes the region. Optional.
        * parent_region_id: string that is the id field for an pre-existing
          region in the backend.  Allows for hierarchical region
          organization
        * enabled: determines whether the endpoint appears in the catalog.
          Defaults to True
    """
    pass


class RegionManager(base.CrudManager):
    """Manager class for manipulating Identity endpoints."""
    resource_class = Region
    collection_key = 'regions'
    key = 'region'

    def create(self, id=None, description=None, enabled=True,
               parent_region=None, **kwargs):
        """Create a Catalog region.

            :param id: a string that identifies the region. If not specified
                a unique identifier will be assigned to the region.
            :param description: a string that describes the region.
            :param parent_region: string that is the id field for a
                pre-existing region in the backend. Allows for hierarchical
                region organization.
            :param enabled: determines whether the endpoint appears in the
                catalog.

        """
        return super(RegionManager, self).create(
            id=id, description=description, enabled=enabled,
            parent_region_id=base.getid(parent_region), **kwargs)

    def get(self, region):
        return super(RegionManager, self).get(
            region_id=base.getid(region))

    def list(self, **kwargs):
        """List regions.

        If ``**kwargs`` are provided, then filter regions with
        attributes matching ``**kwargs``.
        """
        return super(RegionManager, self).list(
            **kwargs)

    def update(self, region, description=None, enabled=None,
               parent_region=None, **kwargs):
        """Update a Catalog region.

            :param region: a string that identifies the region.
            :param description: a string that describes the region.
            :param parent_region: string that is the id field for a
                pre-existing region in the backend.  Allows for hierarchical
                region organization.
            :param enabled: determines whether the endpoint appears in the
                catalog.

        """
        return super(RegionManager, self).update(
            region_id=base.getid(region),
            description=description,
            enabled=enabled,
            parent_region_id=base.getid(parent_region),
            **kwargs)

    def delete(self, region):
        return super(RegionManager, self).delete(
            region_id=base.getid(region))
