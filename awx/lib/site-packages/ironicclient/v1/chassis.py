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


CREATION_ATTRIBUTES = ['description', 'extra']


class Chassis(base.Resource):
    def __repr__(self):
        return "<Chassis %s>" % self._info


class ChassisManager(base.Manager):
    resource_class = Chassis

    @staticmethod
    def _path(id=None):
        return '/v1/chassis/%s' % id if id else '/v1/chassis'

    def list(self, marker=None, limit=None, sort_key=None,
             sort_dir=None, detail=False):
        """Retrieve a list of chassis.

        :param marker: Optional, the UUID of a chassis, eg the last
                       chassis from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of chassis to return.
            2) limit == 0, return the entire list of chassis.
            3) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the Ironic API
               (see Ironic's api.max_limit option).

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :param detail: Optional, boolean whether to return detailed information
                       about chassis.

        :returns: A list of chassis.

        """
        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key, sort_dir)

        path = ''
        if detail:
            path += 'detail'
        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path), "chassis")
        else:
            return self._list_pagination(self._path(path), "chassis",
                                         limit=limit)

    def list_nodes(self, chassis_id, marker=None, limit=None,
                   sort_key=None, sort_dir=None, detail=False):
        """List all the nodes for a given chassis.

        :param chassis_id: The UUID of the chassis.
        :param marker: Optional, the UUID of a node, eg the last
                       node from a previous result set. Return
                       the next result set.
        :param limit: The maximum number of results to return per
                      request, if:

            1) limit > 0, the maximum number of nodes to return.
            2) limit == 0, return the entire list of nodes.
            3) limit param is NOT specified (None), the number of items
               returned respect the maximum imposed by the Ironic API
               (see Ironic's api.max_limit option).

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :param detail: Optional, boolean whether to return detailed information
                       about nodes.

        :returns: A list of nodes.

        """
        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key, sort_dir)

        path = "%s/nodes" % chassis_id
        if detail:
            path += '/detail'

        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path), "nodes")
        else:
            return self._list_pagination(self._path(path), "nodes",
                                         limit=limit)

    def get(self, chassis_id):
        try:
            return self._list(self._path(chassis_id))[0]
        except IndexError:
            return None

    def create(self, **kwargs):
        new = {}
        for (key, value) in kwargs.items():
            if key in CREATION_ATTRIBUTES:
                new[key] = value
            else:
                raise exc.InvalidAttribute()
        return self._create(self._path(), new)

    def delete(self, chassis_id):
        return self._delete(self._path(chassis_id))

    def update(self, chassis_id, patch):
        return self._update(self._path(chassis_id), patch)
