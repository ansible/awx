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


from libcloud.utils.py3 import httplib
from libcloud.common.brightbox import BrightboxConnection
from libcloud.loadbalancer.base import Driver, Algorithm, Member
from libcloud.loadbalancer.base import LoadBalancer
from libcloud.loadbalancer.types import State
from libcloud.utils.misc import reverse_dict

API_VERSION = '1.0'


class BrightboxLBDriver(Driver):
    connectionCls = BrightboxConnection

    name = 'Brightbox'
    website = 'http://www.brightbox.co.uk/'

    LB_STATE_MAP = {
        'creating': State.PENDING,
        'active': State.RUNNING,
        'deleting': State.UNKNOWN,
        'deleted': State.UNKNOWN,
        'failing': State.UNKNOWN,
        'failed': State.UNKNOWN,
    }

    _VALUE_TO_ALGORITHM_MAP = {
        'round-robin': Algorithm.ROUND_ROBIN,
        'least-connections': Algorithm.LEAST_CONNECTIONS
    }

    _ALGORITHM_TO_VALUE_MAP = reverse_dict(_VALUE_TO_ALGORITHM_MAP)

    def list_protocols(self):
        return ['tcp', 'http']

    def list_balancers(self):
        data = self.connection.request('/%s/load_balancers' % API_VERSION) \
                   .object

        return list(map(self._to_balancer, data))

    def create_balancer(self, name, port, protocol, algorithm, members):
        response = self._post(
            '/%s/load_balancers' % API_VERSION,
            {'name': name,
             'nodes': list(map(self._member_to_node, members)),
             'policy': self._algorithm_to_value(algorithm),
             'listeners': [{'in': port, 'out': port, 'protocol': protocol}],
             'healthcheck': {'type': protocol, 'port': port}}
        )

        return self._to_balancer(response.object)

    def destroy_balancer(self, balancer):
        response = self.connection.request('/%s/load_balancers/%s' %
                                           (API_VERSION, balancer.id),
                                           method='DELETE')

        return response.status == httplib.ACCEPTED

    def get_balancer(self, balancer_id):
        data = self.connection.request(
            '/%s/load_balancers/%s' % (API_VERSION, balancer_id)).object
        return self._to_balancer(data)

    def balancer_attach_compute_node(self, balancer, node):
        return self.balancer_attach_member(balancer, node)

    def balancer_attach_member(self, balancer, member):
        path = '/%s/load_balancers/%s/add_nodes' % (API_VERSION, balancer.id)

        self._post(path, {'nodes': [self._member_to_node(member)]})

        return member

    def balancer_detach_member(self, balancer, member):
        path = '/%s/load_balancers/%s/remove_nodes' % (API_VERSION,
                                                       balancer.id)

        response = self._post(path, {'nodes': [self._member_to_node(member)]})

        return response.status == httplib.ACCEPTED

    def balancer_list_members(self, balancer):
        path = '/%s/load_balancers/%s' % (API_VERSION, balancer.id)

        data = self.connection.request(path).object

        func = lambda data: self._node_to_member(data, balancer)
        return list(map(func, data['nodes']))

    def _post(self, path, data={}):
        headers = {'Content-Type': 'application/json'}

        return self.connection.request(path, data=data, headers=headers,
                                       method='POST')

    def _to_balancer(self, data):
        return LoadBalancer(
            id=data['id'],
            name=data['name'],
            state=self.LB_STATE_MAP.get(data['status'], State.UNKNOWN),
            ip=self._public_ip(data),
            port=data['listeners'][0]['in'],
            driver=self.connection.driver
        )

    def _member_to_node(self, member):
        return {'node': member.id}

    def _node_to_member(self, data, balancer):
        return Member(id=data['id'], ip=None, port=None, balancer=balancer)

    def _public_ip(self, data):
        if len(data['cloud_ips']) > 0:
            ip = data['cloud_ips'][0]['public_ip']
        else:
            ip = None

        return ip
