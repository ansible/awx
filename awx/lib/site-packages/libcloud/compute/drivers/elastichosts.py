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

"""
ElasticHosts Driver
"""

from libcloud.compute.types import Provider
from libcloud.compute.drivers.elasticstack import ElasticStackBaseNodeDriver


# API end-points
API_ENDPOINTS = {
    'lon-p': {
        'name': 'London Peer 1',
        'country': 'United Kingdom',
        'host': 'api-lon-p.elastichosts.com'
    },
    'lon-b': {
        'name': 'London BlueSquare',
        'country': 'United Kingdom',
        'host': 'api-lon-b.elastichosts.com'
    },
    'sat-p': {
        'name': 'San Antonio Peer 1',
        'country': 'United States',
        'host': 'api-sat-p.elastichosts.com'
    },
    'lax-p': {
        'name': 'Los Angeles Peer 1',
        'country': 'United States',
        'host': 'api-lax-p.elastichosts.com'
    },
    'sjc-c': {
        'name': 'San Jose (Silicon Valley)',
        'country': 'United States',
        'host': 'api-sjc-c.elastichosts.com'
    },
    'tor-p': {
        'name': 'Toronto Peer 1',
        'country': 'Canada',
        'host': 'api-tor-p.elastichosts.com'
    },
    'syd-y': {
        'name': 'Sydney',
        'country': 'Australia',
        'host': 'api-syd-v.elastichosts.com'
    },
    'cn-1': {
        'name': 'Hong Kong',
        'country': 'China',
        'host': 'api-hkg-e.elastichosts.com'
    }
}

# Default API end-point for the base connection class.
DEFAULT_REGION = 'sat-p'

# Retrieved from http://www.elastichosts.com/cloud-hosting/api
STANDARD_DRIVES = {
    '38df0986-4d85-4b76-b502-3878ffc80161': {
        'uuid': '38df0986-4d85-4b76-b502-3878ffc80161',
        'description': 'CentOS Linux 5.5',
        'size_gunzipped': '3GB',
        'supports_deployment': True,
    },
    '980cf63c-f21e-4382-997b-6541d5809629': {
        'uuid': '980cf63c-f21e-4382-997b-6541d5809629',
        'description': 'Debian Linux 5.0',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    'aee5589a-88c3-43ef-bb0a-9cab6e64192d': {
        'uuid': 'aee5589a-88c3-43ef-bb0a-9cab6e64192d',
        'description': 'Ubuntu Linux 10.04',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    '62f512cd-82c7-498e-88d8-a09ac2ef20e7': {
        'uuid': '62f512cd-82c7-498e-88d8-a09ac2ef20e7',
        'description': 'Ubuntu Linux 12.04',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    'b9d0eb72-d273-43f1-98e3-0d4b87d372c0': {
        'uuid': 'b9d0eb72-d273-43f1-98e3-0d4b87d372c0',
        'description': 'Windows Web Server 2008',
        'size_gunzipped': '13GB',
        'supports_deployment': False,
    },
    '30824e97-05a4-410c-946e-2ba5a92b07cb': {
        'uuid': '30824e97-05a4-410c-946e-2ba5a92b07cb',
        'description': 'Windows Web Server 2008 R2',
        'size_gunzipped': '13GB',
        'supports_deployment': False,
    },
    '9ecf810e-6ad1-40ef-b360-d606f0444671': {
        'uuid': '9ecf810e-6ad1-40ef-b360-d606f0444671',
        'description': 'Windows Web Server 2008 R2 + SQL Server',
        'size_gunzipped': '13GB',
        'supports_deployment': False,
    },
    '10a88d1c-6575-46e3-8d2c-7744065ea530': {
        'uuid': '10a88d1c-6575-46e3-8d2c-7744065ea530',
        'description': 'Windows Server 2008 Standard R2',
        'size_gunzipped': '13GB',
        'supports_deployment': False,
    },
    '2567f25c-8fb8-45c7-95fc-bfe3c3d84c47': {
        'uuid': '2567f25c-8fb8-45c7-95fc-bfe3c3d84c47',
        'description': 'Windows Server 2008 Standard R2 + SQL Server',
        'size_gunzipped': '13GB',
        'supports_deployment': False,
    },
}


class ElasticHostsException(Exception):
    def __str__(self):
        return self.args[0]

    def __repr__(self):
        return "<ElasticHostsException '%s'>" % (self.args[0])


class ElasticHostsNodeDriver(ElasticStackBaseNodeDriver):
    """
    Node Driver class for ElasticHosts
    """
    type = Provider.ELASTICHOSTS
    api_name = 'elastichosts'
    name = 'ElasticHosts'
    website = 'http://www.elastichosts.com/'
    features = {"create_node": ["generates_password"]}
    _standard_drives = STANDARD_DRIVES

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 region=DEFAULT_REGION, **kwargs):

        if hasattr(self, '_region'):
            region = self._region

        if region not in API_ENDPOINTS:
            raise ValueError('Invalid region: %s' % (region))

        self._host_argument_set = host is not None
        super(ElasticHostsNodeDriver, self).__init__(key=key, secret=secret,
                                                     secure=secure, host=host,
                                                     port=port,
                                                     region=region, **kwargs)

    def _ex_connection_class_kwargs(self):
        """
        Return the host value based on the user supplied region.
        """
        kwargs = {}
        if not self._host_argument_set:
            kwargs['host'] = API_ENDPOINTS[self.region]['host']

        return kwargs


class ElasticHostsUK1NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the London Peer 1 end-point
    """
    name = 'ElasticHosts (lon-p)'
    _region = 'lon-p'


class ElasticHostsUK2NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the London Bluesquare end-point
    """
    name = 'ElasticHosts (lon-b)'
    _region = 'lon-b'


class ElasticHostsUS1NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the San Antonio Peer 1 end-point
    """
    name = 'ElasticHosts (sat-p)'
    _region = 'sat-p'


class ElasticHostsUS2NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the Los Angeles Peer 1 end-point
    """
    name = 'ElasticHosts (lax-p)'
    _region = 'lax-p'


class ElasticHostsUS3NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the San Jose (Silicon Valley) end-point
    """
    name = 'ElasticHosts (sjc-c)'
    _region = 'sjc-c'


class ElasticHostsCA1NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the Toronto Peer 1 end-point
    """
    name = 'ElasticHosts (tor-p)'
    _region = 'tor-p'


class ElasticHostsAU1NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the Sydney end-point
    """
    name = 'ElasticHosts (syd-y)'
    _region = 'syd-y'


class ElasticHostsCN1NodeDriver(ElasticHostsNodeDriver):
    """
    ElasticHosts node driver for the Hong Kong end-point
    """
    name = 'ElasticHosts (cn-1)'
    _region = 'cn-1'
