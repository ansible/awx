# -*- coding: utf-8 -*-
#
# Copyright © 2013 Red Hat, Inc
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

from ironicclient.common import base
from ironicclient.common import utils
from ironicclient import exc

CREATION_ATTRIBUTES = ['address', 'extra', 'node_uuid']


class Port(base.Resource):
    def __repr__(self):
        return "<Port %s>" % self._info


class PortManager(base.Manager):
    resource_class = Port

    @staticmethod
    def _path(id=None):
        return '/v1/ports/%s' % id if id else '/v1/ports'

    def list(self, address=None, limit=None, marker=None, sort_key=None,
             sort_dir=None, detail=False):
        """Retrieve a list of port.

        :param address: Optional, MAC address of a port, to get
                       the port which has this MAC address
        :param marker: Optional, the UUID of a port, eg the last
                       port from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of ports to return.
            2) limit == 0, return the entire list of ports.
            3) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the Ironic API
               (see Ironic's api.max_limit option).

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :param detail: Optional, boolean whether to return detailed information
                       about ports.

        :returns: A list of ports.

        """
        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key, sort_dir)
        if address is not None:
            filters.append('address=%s' % address)

        path = ''
        if detail:
            path += 'detail'
        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path), "ports")
        else:
            return self._list_pagination(self._path(path), "ports",
                                         limit=limit)

    def get(self, port_id):
        try:
            return self._list(self._path(port_id))[0]
        except IndexError:
            return None

    def get_by_address(self, address):
        path = "detail?address=%s" % address
        ports = self._list(self._path(path), 'ports')
        # get all the details of the port assuming that filtering by
        # address returns a collection of one port if successful.
        if len(ports) == 1:
            return ports[0]
        else:
            raise exc.NotFound()

    def create(self, **kwargs):
        new = {}
        for (key, value) in kwargs.items():
            if key in CREATION_ATTRIBUTES:
                new[key] = value
            else:
                raise exc.InvalidAttribute()
        return self._create(self._path(), new)

    def delete(self, port_id):
        return self._delete(self._path(port_id))

    def update(self, port_id, patch):
        return self._update(self._path(port_id), patch)
