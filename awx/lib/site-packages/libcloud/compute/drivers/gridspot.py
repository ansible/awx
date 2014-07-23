# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from libcloud.compute.base import NodeDriver, Node
from libcloud.compute.base import NodeState
from libcloud.common.base import ConnectionKey, JsonResponse
from libcloud.compute.types import Provider
from libcloud.common.types import InvalidCredsError


class GridspotAPIException(Exception):
    def __str__(self):
        return self.args[0]

    def __repr__(self):
        return "<GridspotAPIException '%s'>" % (self.args[0])


class GridspotResponse(JsonResponse):
    """
    Response class for Gridspot
    """
    def parse_body(self):
        body = super(GridspotResponse, self).parse_body()

        if 'exception_name' in body and body['exception_name']:
            raise GridspotAPIException(body['exception_name'])

        return body

    def parse_error(self):
        # Gridspot 404s on invalid api key or instance_id
        raise InvalidCredsError("Invalid api key/instance_id")


class GridspotConnection(ConnectionKey):
    """
    Connection class to connect to Gridspot's API servers
    """

    host = 'gridspot.com'
    responseCls = GridspotResponse

    def add_default_params(self, params):
        params['api_key'] = self.key
        return params


class GridspotNodeDriver(NodeDriver):
    """
    Gridspot (http://www.gridspot.com/) node driver.
    """

    type = Provider.GRIDSPOT
    name = 'Gridspot'
    website = 'http://www.gridspot.com/'
    connectionCls = GridspotConnection
    NODE_STATE_MAP = {
        'Running': NodeState.RUNNING,
        'Starting': NodeState.PENDING
    }

    def list_nodes(self):
        data = self.connection.request(
            '/compute_api/v1/list_instances').object
        return [self._to_node(n) for n in data['instances']]

    def destroy_node(self, node):
        data = {'instance_id': node.id}
        self.connection.request('/compute_api/v1/stop_instance', data).object
        return True

    def _get_node_state(self, state):
        result = self.NODE_STATE_MAP.get(state, NodeState.UNKNOWN)
        return result

    def _add_int_param(self, params, data, field):
        if data[field]:
            try:
                params[field] = int(data[field])
            except:
                pass

    def _to_node(self, data):
        port = None
        ip = None

        state = self._get_node_state(data['current_state'])

        if data['vm_ssh_wan_ip_endpoint'] != 'null':
            parts = data['vm_ssh_wan_ip_endpoint'].split(':')
            ip = parts[0]
            port = int(parts[1])

        extra_params = {
            'winning_bid_id': data['winning_bid_id'],
            'port': port
        }

        # Spec is vague and doesn't indicate if these will always be present
        self._add_int_param(extra_params, data, 'vm_num_logical_cores')
        self._add_int_param(extra_params, data, 'vm_num_physical_cores')
        self._add_int_param(extra_params, data, 'vm_ram')
        self._add_int_param(extra_params, data, 'start_state_time')
        self._add_int_param(extra_params, data, 'ended_state_time')
        self._add_int_param(extra_params, data, 'running_state_time')

        return Node(
            id=data['instance_id'],
            name=data['instance_id'],
            state=state,
            public_ips=[ip],
            private_ips=[],
            driver=self.connection.driver,
            extra=extra_params)
