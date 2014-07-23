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

from libcloud.common.types import LibcloudError
from libcloud.storage.providers import Provider

from libcloud.storage.drivers.cloudfiles import CloudFilesConnection
from libcloud.storage.drivers.cloudfiles import CloudFilesStorageDriver

KTUCLOUDSTORAGE_AUTH_URL = "https://ssproxy.ucloudbiz.olleh.com/auth/v1.0"
KTUCLOUDSTORAGE_API_VERSION = "1.0"


class KTUCloudStorageConnection(CloudFilesConnection):
    """
    Connection class for the KT UCloud Storage endpoint.
    """

    auth_url = KTUCLOUDSTORAGE_AUTH_URL
    _auth_version = KTUCLOUDSTORAGE_API_VERSION

    def get_endpoint(self):
        eps = self.service_catalog.get_endpoints(name='cloudFiles')
        if len(eps) == 0:
            raise LibcloudError('Could not find specified endpoint')
        ep = eps[0]
        if 'publicURL' in ep:
            return ep['publicURL']
        else:
            raise LibcloudError('Could not find specified endpoint')


class KTUCloudStorageDriver(CloudFilesStorageDriver):
    """
    Cloudfiles storage driver for the UK endpoint.
    """

    type = Provider.KTUCLOUD
    name = 'KTUCloud Storage'
    connectionCls = KTUCloudStorageConnection
