# Copyright 2012 OpenStack Foundation
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

"""Aggregate interface."""

from novaclient import base


class Aggregate(base.Resource):
    """An aggregates is a collection of compute hosts."""

    def __repr__(self):
        return "<Aggregate: %s>" % self.id

    def update(self, values):
        """Update the name and/or availability zone."""
        return self.manager.update(self, values)

    def add_host(self, host):
        return self.manager.add_host(self, host)

    def remove_host(self, host):
        return self.manager.remove_host(self, host)

    def set_metadata(self, metadata):
        return self.manager.set_metadata(self, metadata)

    def delete(self):
        self.manager.delete(self)


class AggregateManager(base.ManagerWithFind):
    resource_class = Aggregate

    def list(self):
        """Get a list of os-aggregates."""
        return self._list('/os-aggregates', 'aggregates')

    def create(self, name, availability_zone):
        """Create a new aggregate."""
        body = {'aggregate': {'name': name,
                              'availability_zone': availability_zone}}
        return self._create('/os-aggregates', body, 'aggregate')

    def get(self, aggregate):
        """Get details of the specified aggregate."""
        return self._get('/os-aggregates/%s' % (base.getid(aggregate)),
                         "aggregate")

    # NOTE:(dtroyer): utils.find_resource() uses manager.get() but we need to
    #                 keep the API backward compatible
    def get_details(self, aggregate):
        """Get details of the specified aggregate."""
        return self.get(aggregate)

    def update(self, aggregate, values):
        """Update the name and/or availability zone."""
        body = {'aggregate': values}
        return self._update("/os-aggregates/%s" % base.getid(aggregate),
                            body,
                            "aggregate")

    def add_host(self, aggregate, host):
        """Add a host into the Host Aggregate."""
        body = {'add_host': {'host': host}}
        return self._create("/os-aggregates/%s/action" % base.getid(aggregate),
                            body, "aggregate")

    def remove_host(self, aggregate, host):
        """Remove a host from the Host Aggregate."""
        body = {'remove_host': {'host': host}}
        return self._create("/os-aggregates/%s/action" % base.getid(aggregate),
                            body, "aggregate")

    def set_metadata(self, aggregate, metadata):
        """Set a aggregate metadata, replacing the existing metadata."""
        body = {'set_metadata': {'metadata': metadata}}
        return self._create("/os-aggregates/%s/action" % base.getid(aggregate),
                            body, "aggregate")

    def delete(self, aggregate):
        """Delete the specified aggregates."""
        self._delete('/os-aggregates/%s' % (base.getid(aggregate)))
