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

import hashlib
import time

from libcloud.utils.py3 import b

from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.common.types import MalformedResponseError
from libcloud.common.base import ConnectionUserAndKey, JsonResponse
from libcloud.compute.base import NodeLocation

HOST = 'api.gogrid.com'
PORTS_BY_SECURITY = {True: 443, False: 80}
API_VERSION = '1.8'

__all__ = [
    "GoGridResponse",
    "GoGridConnection",
    "GoGridIpAddress",
    "BaseGoGridDriver",
]


class GoGridResponse(JsonResponse):

    def __init__(self, *args, **kwargs):
        self.driver = BaseGoGridDriver
        super(GoGridResponse, self).__init__(*args, **kwargs)

    def success(self):
        if self.status == 403:
            raise InvalidCredsError('Invalid credentials', self.driver)
        if self.status == 401:
            raise InvalidCredsError('API Key has insufficient rights',
                                    self.driver)
        if not self.body:
            return None
        try:
            return self.parse_body()['status'] == 'success'
        except ValueError:
            raise MalformedResponseError('Malformed reply',
                                         body=self.body,
                                         driver=self.driver)

    def parse_error(self):
        try:
            return self.parse_body()["list"][0]["message"]
        except (ValueError, KeyError):
            return None


class GoGridConnection(ConnectionUserAndKey):
    """
    Connection class for the GoGrid driver
    """

    host = HOST
    responseCls = GoGridResponse

    def add_default_params(self, params):
        params["api_key"] = self.user_id
        params["v"] = API_VERSION
        params["format"] = 'json'
        params["sig"] = self.get_signature(self.user_id, self.key)

        return params

    def get_signature(self, key, secret):
        """ create sig from md5 of key + secret + time """
        m = hashlib.md5(b(key + secret + str(int(time.time()))))
        return m.hexdigest()

    def request(self, action, params=None, data='', headers=None, method='GET',
                raw=False):
        return super(GoGridConnection, self).request(action, params, data,
                                                     headers, method, raw)


class GoGridIpAddress(object):
    """
    IP Address
    """

    def __init__(self, id, ip, public, state, subnet):
        self.id = id
        self.ip = ip
        self.public = public
        self.state = state
        self.subnet = subnet


class BaseGoGridDriver(object):
    """GoGrid has common object model for services they
    provide, like locations and IP, so keep handling of
    these things in a single place."""

    name = "GoGrid"

    def _get_ip(self, element):
        return element.get('ip').get('ip')

    def _to_ip(self, element):
        ip = GoGridIpAddress(id=element['id'],
                             ip=element['ip'],
                             public=element['public'],
                             subnet=element['subnet'],
                             state=element["state"]["name"])
        ip.location = self._to_location(element['datacenter'])
        return ip

    def _to_ips(self, object):
        return [self._to_ip(el)
                for el in object['list']]

    def _to_location(self, element):
        location = NodeLocation(id=element['id'],
                                name=element['name'],
                                country="US",
                                driver=self.connection.driver)
        return location

    def _to_locations(self, object):
        return [self._to_location(el)
                for el in object['list']]

    def ex_list_ips(self, **kwargs):
        """Return list of IP addresses assigned to
        the account.

        :keyword    public: set to True to list only
                    public IPs or False to list only
                    private IPs. Set to None or not specify
                    at all not to filter by type
        :type       public: ``bool``

        :keyword    assigned: set to True to list only addresses
                    assigned to servers, False to list unassigned
                    addresses and set to None or don't set at all
                    not no filter by state
        :type       assigned: ``bool``

        :keyword    location: filter IP addresses by location
        :type       location: :class:`NodeLocation`

        :rtype: ``list`` of :class:`GoGridIpAddress`
        """

        params = {}

        if "public" in kwargs and kwargs["public"] is not None:
            params["ip.type"] = {True: "Public",
                                 False: "Private"}[kwargs["public"]]
        if "assigned" in kwargs and kwargs["assigned"] is not None:
            params["ip.state"] = {True: "Assigned",
                                  False: "Unassigned"}[kwargs["assigned"]]
        if "location" in kwargs and kwargs['location'] is not None:
            params['datacenter'] = kwargs['location'].id

        response = self.connection.request('/api/grid/ip/list', params=params)
        ips = self._to_ips(response.object)
        return ips

    def _get_first_ip(self, location=None):
        ips = self.ex_list_ips(public=True, assigned=False, location=location)
        try:
            return ips[0].ip
        except IndexError:
            raise LibcloudError('No public unassigned IPs left',
                                self.driver)
