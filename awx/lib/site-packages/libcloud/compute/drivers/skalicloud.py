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
skalicloud Driver
"""

from libcloud.compute.types import Provider
from libcloud.compute.drivers.elasticstack import ElasticStackBaseNodeDriver
from libcloud.compute.drivers.elasticstack import ElasticStackBaseConnection


# API end-points
API_ENDPOINTS = {
    'my-1': {
        'name': 'Malaysia, Kuala Lumpur',
        'country': 'Malaysia',
        'host': 'api.sdg-my.skalicloud.com'
    }
}

# Default API end-point for the base connection class.
DEFAULT_ENDPOINT = 'my-1'

# Retrieved from http://www.skalicloud.com/cloud-api/
STANDARD_DRIVES = {
    '90aa51f2-15c0-4cff-81ee-e93aa20b9468': {
        'uuid': '90aa51f2-15c0-4cff-81ee-e93aa20b9468',
        'description': 'CentOS 5.5 -64bit',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    'c144d7a7-e24b-48ab-954b-6b6ec514ed6f': {
        'uuid': 'c144d7a7-e24b-48ab-954b-6b6ec514ed6f',
        'description': 'Debian 5 -64bit',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    '3051699a-a536-4220-aeb5-67f2ec101a09': {
        'uuid': '3051699a-a536-4220-aeb5-67f2ec101a09',
        'description': 'Ubuntu Server 10.10 -64bit',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    '11c4c922-5ff8-4094-b06c-eb8ffaec1ea9': {
        'uuid': '11c4c922-5ff8-4094-b06c-eb8ffaec1ea9',
        'description': 'Windows 2008R2 Web Edition',
        'size_gunzipped': '13GB',
        'supports_deployment': False,
    },
    '93bf390e-4f46-4252-a8bc-9d6d80e3f955': {
        'uuid': '93bf390e-4f46-4252-a8bc-9d6d80e3f955',
        'description': 'Windows Server 2008R2 Standard',
        'size_gunzipped': '13GB',
        'supports_deployment': False,
    }
}


class SkaliCloudConnection(ElasticStackBaseConnection):
    host = API_ENDPOINTS[DEFAULT_ENDPOINT]['host']


class SkaliCloudNodeDriver(ElasticStackBaseNodeDriver):
    type = Provider.SKALICLOUD
    api_name = 'skalicloud'
    name = 'skalicloud'
    website = 'http://www.skalicloud.com/'
    connectionCls = SkaliCloudConnection
    features = {"create_node": ["generates_password"]}
    _standard_drives = STANDARD_DRIVES
