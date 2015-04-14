# -*- coding: utf-8 -*-
#
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

import os

from ironicclient.common import base
from ironicclient.common.i18n import _
from ironicclient.common import utils
from ironicclient import exc

CREATION_ATTRIBUTES = ['chassis_uuid', 'driver', 'driver_info', 'extra',
                       'uuid', 'properties', 'name']


class Node(base.Resource):
    def __repr__(self):
        return "<Node %s>" % self._info


class NodeManager(base.Manager):
    resource_class = Node

    @staticmethod
    def _path(id=None):
        return '/v1/nodes/%s' % id if id else '/v1/nodes'

    def list(self, associated=None, maintenance=None, marker=None, limit=None,
             detail=False, sort_key=None, sort_dir=None):
        """Retrieve a list of nodes.

        :param associated: Optional, boolean whether to return a list of
                           associated or unassociated nodes.
        :param maintenance: Optional, boolean value that indicates whether
                            to get nodes in maintenance mode ("True"), or not
                            in maintenance mode ("False").
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

        :param detail: Optional, boolean whether to return detailed information
                       about nodes.

        :param sort_key: Optional, field used for sorting.

        :param sort_dir: Optional, direction of sorting, either 'asc' (the
                         default) or 'desc'.

        :returns: A list of nodes.

        """
        if limit is not None:
            limit = int(limit)

        filters = utils.common_filters(marker, limit, sort_key, sort_dir)
        if associated is not None:
            filters.append('associated=%s' % associated)
        if maintenance is not None:
            filters.append('maintenance=%s' % maintenance)

        path = ''
        if detail:
            path += 'detail'
        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path), "nodes")
        else:
            return self._list_pagination(self._path(path), "nodes",
                                         limit=limit)

    def list_ports(self, node_id, marker=None, limit=None, sort_key=None,
                   sort_dir=None, detail=False):
        """List all the ports for a given node.

        :param node_id: The UUID of the node.
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

        path = "%s/ports" % node_id
        if detail:
            path += '/detail'

        if filters:
            path += '?' + '&'.join(filters)

        if limit is None:
            return self._list(self._path(path), "ports")
        else:
            return self._list_pagination(self._path(path), "ports",
                                         limit=limit)

    def get(self, node_id):
        try:
            return self._list(self._path(node_id))[0]
        except IndexError:
            return None

    def get_by_instance_uuid(self, instance_uuid):
        path = "detail?instance_uuid=%s" % instance_uuid
        nodes = self._list(self._path(path), 'nodes')
        # get all the details of the node assuming that
        # filtering by instance_uuid returns a collection
        # of one node if successful.
        if len(nodes) == 1:
            return nodes[0]
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

    def delete(self, node_id):
        return self._delete(self._path(node_id))

    def update(self, node_id, patch, http_method='PATCH'):
        return self._update(self._path(node_id), patch, method=http_method)

    def vendor_passthru(self, node_id, method, args=None, http_method=None):
        """Issue requests for vendor-specific actions on a given node.

        :param node_id: The UUID of the node.
        :param method: Name of the vendor method.
        :param args: Optional. The arguments to be passed to the method.
        :param http_method: The HTTP method to use on the request.
                            Defaults to POST.

        """
        if args is None:
            args = {}

        if http_method is None:
            http_method = 'POST'

        http_method = http_method.upper()

        path = "%s/vendor_passthru/%s" % (node_id, method)
        if http_method in ('POST', 'PUT', 'PATCH'):
            return self.update(path, args, http_method=http_method)
        elif http_method == 'DELETE':
            return self.delete(path)
        elif http_method == 'GET':
            return self.get(path)
        else:
            raise exc.InvalidAttribute(
                _('Unknown HTTP method: %s') % http_method)

    def set_maintenance(self, node_id, state, maint_reason=None):
        path = "%s/maintenance" % node_id
        if state in ('true', 'on'):
            reason = {'reason': maint_reason}
            return self._update(self._path(path), reason, method='PUT')
        if state in ('false', 'off'):
            return self._delete(self._path(path))

    def set_power_state(self, node_id, state):
        path = "%s/states/power" % node_id
        if state in ['on', 'off']:
            state = "power %s" % state
        if state in ['reboot']:
            state = "rebooting"
        target = {'target': state}
        return self._update(self._path(path), target, method='PUT')

    def validate(self, node_uuid):
        path = "%s/validate" % node_uuid
        return self.get(path)

    def set_provision_state(self, node_uuid, state, configdrive=None):
        path = "%s/states/provision" % node_uuid
        body = {'target': state}
        if configdrive:
            if os.path.isfile(configdrive):
                with open(configdrive, 'rb') as f:
                    configdrive = f.read()
            if os.path.isdir(configdrive):
                configdrive = utils.make_configdrive(configdrive)

            body['configdrive'] = configdrive
        return self._update(self._path(path), body, method='PUT')

    def states(self, node_uuid):
        path = "%s/states" % node_uuid
        return self.get(path)

    def get_console(self, node_uuid):
        path = "%s/states/console" % node_uuid
        info = self.get(path)
        if not info:
            return {}
        return info.to_dict()

    def set_console_mode(self, node_uuid, enabled):
        path = "%s/states/console" % node_uuid
        target = {'enabled': enabled}
        return self._update(self._path(path), target, method='PUT')

    def set_boot_device(self, node_uuid, boot_device, persistent=False):
        path = "%s/management/boot_device" % node_uuid
        target = {'boot_device': boot_device, 'persistent': persistent}
        return self._update(self._path(path), target, method='PUT')

    def get_boot_device(self, node_uuid):
        path = "%s/management/boot_device" % node_uuid
        return self.get(path).to_dict()

    def get_supported_boot_devices(self, node_uuid):
        path = "%s/management/boot_device/supported" % node_uuid
        return self.get(path).to_dict()
