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
Rackspace driver
"""
from libcloud.compute.types import Provider, LibcloudError
from libcloud.compute.base import NodeLocation, VolumeSnapshot
from libcloud.compute.drivers.openstack import OpenStack_1_0_Connection,\
    OpenStack_1_0_NodeDriver, OpenStack_1_0_Response
from libcloud.compute.drivers.openstack import OpenStack_1_1_Connection,\
    OpenStack_1_1_NodeDriver

from libcloud.common.rackspace import AUTH_URL


ENDPOINT_ARGS_MAP = {
    'dfw': {'service_type': 'compute',
            'name': 'cloudServersOpenStack',
            'region': 'DFW'},
    'ord': {'service_type': 'compute',
            'name': 'cloudServersOpenStack',
            'region': 'ORD'},
    'iad': {'service_type': 'compute',
            'name': 'cloudServersOpenStack',
            'region': 'IAD'},
    'lon': {'service_type': 'compute',
            'name': 'cloudServersOpenStack',
            'region': 'LON'},
    'syd': {'service_type': 'compute',
            'name': 'cloudServersOpenStack',
            'region': 'SYD'},
    'hkg': {'service_type': 'compute',
            'name': 'cloudServersOpenStack',
            'region': 'HKG'},

}


class RackspaceFirstGenConnection(OpenStack_1_0_Connection):
    """
    Connection class for the Rackspace first-gen driver.
    """
    responseCls = OpenStack_1_0_Response
    XML_NAMESPACE = 'http://docs.rackspacecloud.com/servers/api/v1.0'
    auth_url = AUTH_URL
    _auth_version = '2.0'
    cache_busting = True

    def __init__(self, *args, **kwargs):
        self.region = kwargs.pop('region', None)
        super(RackspaceFirstGenConnection, self).__init__(*args, **kwargs)

    def get_endpoint(self):
        ep = {}

        if '2.0' in self._auth_version:
            ep = self.service_catalog.get_endpoint(service_type='compute',
                                                   name='cloudServers')
        else:
            raise LibcloudError(
                'Auth version "%s" not supported' % (self._auth_version))

        public_url = ep.get('publicURL', None)

        if not public_url:
            raise LibcloudError('Could not find specified endpoint')

        # This is a nasty hack, but it's required because of how the
        # auth system works.
        # Old US accounts can access UK API endpoint, but they don't
        # have this endpoint in the service catalog. Same goes for the
        # old UK accounts and US endpoint.
        if self.region == 'us':
            # Old UK account, which only have uk endpoint in the catalog
            public_url = public_url.replace('https://lon.servers.api',
                                            'https://servers.api')
        elif self.region == 'uk':
            # Old US account, which only has us endpoints in the catalog
            public_url = public_url.replace('https://servers.api',
                                            'https://lon.servers.api')

        return public_url


class RackspaceFirstGenNodeDriver(OpenStack_1_0_NodeDriver):
    name = 'Rackspace Cloud (First Gen)'
    website = 'http://www.rackspace.com'
    connectionCls = RackspaceFirstGenConnection
    type = Provider.RACKSPACE_FIRST_GEN
    api_name = 'rackspace'

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 region='us', **kwargs):
        """
        @inherits:  :class:`NodeDriver.__init__`

        :param region: Region ID which should be used
        :type region: ``str``
        """
        if region not in ['us', 'uk']:
            raise ValueError('Invalid region: %s' % (region))

        super(RackspaceFirstGenNodeDriver, self).__init__(key=key,
                                                          secret=secret,
                                                          secure=secure,
                                                          host=host,
                                                          port=port,
                                                          region=region,
                                                          **kwargs)

    def list_locations(self):
        """
        Lists available locations

        Locations cannot be set or retrieved via the API, but currently
        there are two locations, DFW and ORD.

        @inherits: :class:`OpenStack_1_0_NodeDriver.list_locations`
        """
        if self.region == 'us':
            locations = [NodeLocation(0, "Rackspace DFW1/ORD1", 'US', self)]
        elif self.region == 'uk':
            locations = [NodeLocation(0, 'Rackspace UK London', 'UK', self)]

        return locations

    def _ex_connection_class_kwargs(self):
        kwargs = self.openstack_connection_kwargs()
        kwargs['region'] = self.region
        return kwargs


class RackspaceConnection(OpenStack_1_1_Connection):
    """
    Connection class for the Rackspace next-gen OpenStack base driver.
    """

    auth_url = AUTH_URL
    _auth_version = '2.0'

    def __init__(self, *args, **kwargs):
        self.region = kwargs.pop('region', None)
        self.get_endpoint_args = kwargs.pop('get_endpoint_args', None)
        super(RackspaceConnection, self).__init__(*args, **kwargs)

    def get_endpoint(self):
        if not self.get_endpoint_args:
            raise LibcloudError(
                'RackspaceConnection must have get_endpoint_args set')

        if '2.0' in self._auth_version:
            ep = self.service_catalog.get_endpoint(**self.get_endpoint_args)
        else:
            raise LibcloudError(
                'Auth version "%s" not supported' % (self._auth_version))

        public_url = ep.get('publicURL', None)

        if not public_url:
            raise LibcloudError('Could not find specified endpoint')

        return public_url


class RackspaceNodeDriver(OpenStack_1_1_NodeDriver):
    name = 'Rackspace Cloud (Next Gen)'
    website = 'http://www.rackspace.com'
    connectionCls = RackspaceConnection
    type = Provider.RACKSPACE

    _networks_url_prefix = '/os-networksv2'

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 region='dfw', **kwargs):
        """
        @inherits:  :class:`NodeDriver.__init__`

        :param region: ID of the region which should be used.
        :type region: ``str``
        """
        valid_regions = ENDPOINT_ARGS_MAP.keys()

        if region not in valid_regions:
            raise ValueError('Invalid region: %s' % (region))

        if region == 'lon':
            self.api_name = 'rackspacenovalon'
        elif region == 'syd':
            self.api_name = 'rackspacenovasyd'
        else:
            self.api_name = 'rackspacenovaus'

        super(RackspaceNodeDriver, self).__init__(key=key, secret=secret,
                                                  secure=secure, host=host,
                                                  port=port,
                                                  region=region,
                                                  **kwargs)

    def _to_snapshot(self, api_node):
        if 'snapshot' in api_node:
            api_node = api_node['snapshot']

        extra = {'volume_id': api_node['volumeId'],
                 'name': api_node['displayName'],
                 'created': api_node['createdAt'],
                 'description': api_node['displayDescription'],
                 'status': api_node['status']}

        snapshot = VolumeSnapshot(id=api_node['id'], driver=self,
                                  size=api_node['size'],
                                  extra=extra)
        return snapshot

    def _ex_connection_class_kwargs(self):
        endpoint_args = ENDPOINT_ARGS_MAP[self.region]
        kwargs = self.openstack_connection_kwargs()
        kwargs['region'] = self.region
        kwargs['get_endpoint_args'] = endpoint_args
        return kwargs
