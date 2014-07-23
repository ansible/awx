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
HP Public cloud driver which is esentially just a small wrapper around
OpenStack driver.
"""

from libcloud.compute.types import Provider, LibcloudError
from libcloud.compute.drivers.openstack import OpenStack_1_1_Connection
from libcloud.compute.drivers.openstack import OpenStack_1_1_NodeDriver


__all__ = [
    'HPCloudNodeDriver'
]

ENDPOINT_ARGS_MAP = {
    'region-a.geo-1': {
        'service_type': 'compute',
        'name': 'Compute',
        'region': 'region-a.geo-1'
    },
    'region-b.geo-1': {
        'service_type': 'compute',
        'name': 'Compute',
        'region': 'region-b.geo-1'
    },
}

AUTH_URL_TEMPLATE = 'https://%s.identity.hpcloudsvc.com:35357/v2.0/tokens'


class HPCloudConnection(OpenStack_1_1_Connection):
    _auth_version = '2.0_password'

    def __init__(self, *args, **kwargs):
        self.region = kwargs.pop('region', None)
        self.get_endpoint_args = kwargs.pop('get_endpoint_args', None)
        super(HPCloudConnection, self).__init__(*args, **kwargs)

    def get_endpoint(self):
        if not self.get_endpoint_args:
            raise LibcloudError(
                'HPCloudConnection must have get_endpoint_args set')

        if '2.0_password' in self._auth_version:
            ep = self.service_catalog.get_endpoint(**self.get_endpoint_args)
        else:
            raise LibcloudError(
                'Auth version "%s" not supported' % (self._auth_version))

        public_url = ep.get('publicURL', None)

        if not public_url:
            raise LibcloudError('Could not find specified endpoint')

        return public_url


class HPCloudNodeDriver(OpenStack_1_1_NodeDriver):
    name = 'HP Public Cloud (Helion)'
    website = 'http://www.hpcloud.com/'
    connectionCls = HPCloudConnection
    type = Provider.HPCLOUD

    def __init__(self, key, secret, tenant_name, secure=True,
                 host=None, port=None, region='region-b.geo-1', **kwargs):
        """
        Note: tenant_name argument is required for HP cloud.
        """
        self.tenant_name = tenant_name
        super(HPCloudNodeDriver, self).__init__(key=key, secret=secret,
                                                secure=secure, host=host,
                                                port=port,
                                                region=region,
                                                **kwargs)

    def _ex_connection_class_kwargs(self):
        endpoint_args = ENDPOINT_ARGS_MAP[self.region]

        kwargs = self.openstack_connection_kwargs()
        kwargs['region'] = self.region
        kwargs['get_endpoint_args'] = endpoint_args
        kwargs['ex_force_auth_url'] = AUTH_URL_TEMPLATE % (self.region)
        kwargs['ex_tenant_name'] = self.tenant_name

        return kwargs
