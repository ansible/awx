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

import sys
import time

from libcloud.utils.py3 import httplib

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.utils.misc import reverse_dict
from libcloud.common.types import LibcloudError
from libcloud.common.gogrid import GoGridConnection, GoGridResponse,\
    BaseGoGridDriver
from libcloud.loadbalancer.base import LoadBalancer, Member, Driver, Algorithm
from libcloud.loadbalancer.base import DEFAULT_ALGORITHM
from libcloud.loadbalancer.types import State, LibcloudLBImmutableError


class GoGridLBResponse(GoGridResponse):
    def success(self):
        if self.status == httplib.INTERNAL_SERVER_ERROR:
            # Hack, but at least this error message is more useful than
            # "unexpected server error"
            body = json.loads(self.body)
            if body['method'] == '/grid/loadbalancer/add' and \
                len(body['list']) >= 1 and \
                body['list'][0]['message'].find(
                    'unexpected server error') != -1:
                raise LibcloudError(
                    value='You mostly likely tried to add a member with an IP'
                          ' address not assigned to your account', driver=self)
        return super(GoGridLBResponse, self).success()


class GoGridLBConnection(GoGridConnection):
    """
    Connection class for the GoGrid load-balancer driver.
    """
    responseCls = GoGridLBResponse


class GoGridLBDriver(BaseGoGridDriver, Driver):
    connectionCls = GoGridLBConnection
    api_name = 'gogrid_lb'
    name = 'GoGrid LB'
    website = 'http://www.gogrid.com/'

    LB_STATE_MAP = {'On': State.RUNNING,
                    'Unknown': State.UNKNOWN}
    _VALUE_TO_ALGORITHM_MAP = {
        'round robin': Algorithm.ROUND_ROBIN,
        'least connect': Algorithm.LEAST_CONNECTIONS
    }
    _ALGORITHM_TO_VALUE_MAP = reverse_dict(_VALUE_TO_ALGORITHM_MAP)

    def __init__(self, *args, **kwargs):
        """
        @inherits: :class:`Driver.__init__`
        """
        super(GoGridLBDriver, self).__init__(*args, **kwargs)

    def list_protocols(self):
        # GoGrid only supports http
        return ['http']

    def list_balancers(self):
        return self._to_balancers(
            self.connection.request('/api/grid/loadbalancer/list').object)

    def ex_create_balancer_nowait(self, name, members, protocol='http',
                                  port=80, algorithm=DEFAULT_ALGORITHM):
        """
        @inherits: :class:`Driver.create_balancer`
        """
        algorithm = self._algorithm_to_value(algorithm)

        params = {'name': name,
                  'loadbalancer.type': algorithm,
                  'virtualip.ip': self._get_first_ip(),
                  'virtualip.port': port}
        params.update(self._members_to_params(members))

        resp = self.connection.request('/api/grid/loadbalancer/add',
                                       method='GET',
                                       params=params)
        return self._to_balancers(resp.object)[0]

    def create_balancer(self, name, members, protocol='http', port=80,
                        algorithm=DEFAULT_ALGORITHM):
        balancer = self.ex_create_balancer_nowait(name, members, protocol,
                                                  port, algorithm)

        timeout = 60 * 20
        waittime = 0
        interval = 2 * 15

        if balancer.id is not None:
            return balancer
        else:
            while waittime < timeout:
                balancers = self.list_balancers()

                for i in balancers:
                    if i.name == balancer.name and i.id is not None:
                        return i

                waittime += interval
                time.sleep(interval)

        raise Exception('Failed to get id')

    def destroy_balancer(self, balancer):
        try:
            resp = self.connection.request(
                '/api/grid/loadbalancer/delete', method='POST',
                params={'id': balancer.id})
        except Exception:
            e = sys.exc_info()[1]
            if "Update request for LoadBalancer" in str(e):
                raise LibcloudLBImmutableError(
                    "Cannot delete immutable object", GoGridLBDriver)
            else:
                raise

        return resp.status == 200

    def get_balancer(self, **kwargs):
        params = {}

        try:
            params['name'] = kwargs['ex_balancer_name']
        except KeyError:
            balancer_id = kwargs['balancer_id']
            params['id'] = balancer_id

        resp = self.connection.request('/api/grid/loadbalancer/get',
                                       params=params)

        return self._to_balancers(resp.object)[0]

    def balancer_attach_member(self, balancer, member):
        members = self.balancer_list_members(balancer)
        members.append(member)

        params = {"id": balancer.id}

        params.update(self._members_to_params(members))

        resp = self._update_balancer(params)
        return [m for m in
                self._to_members(resp.object["list"][0]["realiplist"],
                                 balancer)
                if m.ip == member.ip][0]

    def balancer_detach_member(self, balancer, member):
        members = self.balancer_list_members(balancer)

        remaining_members = [n for n in members if n.id != member.id]

        params = {"id": balancer.id}
        params.update(self._members_to_params(remaining_members))

        resp = self._update_balancer(params)

        return resp.status == 200

    def balancer_list_members(self, balancer):
        resp = self.connection.request('/api/grid/loadbalancer/get',
                                       params={'id': balancer.id})
        return self._to_members(resp.object["list"][0]["realiplist"], balancer)

    def _update_balancer(self, params):
        try:
            return self.connection.request('/api/grid/loadbalancer/edit',
                                           method='POST',
                                           params=params)
        except Exception:
            e = sys.exc_info()[1]
            if "Update already pending" in str(e):
                raise LibcloudLBImmutableError(
                    "Balancer is immutable", GoGridLBDriver)

        raise LibcloudError(value='Exception: %s' % str(e), driver=self)

    def _members_to_params(self, members):
        """
        Helper method to convert list of :class:`Member` objects
        to GET params.

        """

        params = {}

        i = 0
        for member in members:
            params["realiplist.%s.ip" % i] = member.ip
            params["realiplist.%s.port" % i] = member.port
            i += 1

        return params

    def _to_balancers(self, object):
        return [self._to_balancer(el) for el in object["list"]]

    def _to_balancer(self, el):
        lb = LoadBalancer(id=el.get("id"),
                          name=el["name"],
                          state=self.LB_STATE_MAP.get(
                              el["state"]["name"], State.UNKNOWN),
                          ip=el["virtualip"]["ip"]["ip"],
                          port=el["virtualip"]["port"],
                          driver=self.connection.driver)
        return lb

    def _to_members(self, object, balancer=None):
        return [self._to_member(el, balancer) for el in object]

    def _to_member(self, el, balancer=None):
        member = Member(id=el["ip"]["id"],
                        ip=el["ip"]["ip"],
                        port=el["port"],
                        balancer=balancer)
        return member
