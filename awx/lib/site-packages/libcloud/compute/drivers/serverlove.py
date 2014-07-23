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
ServerLove Driver
"""

from libcloud.compute.types import Provider
from libcloud.compute.drivers.elasticstack import ElasticStackBaseNodeDriver
from libcloud.compute.drivers.elasticstack import ElasticStackBaseConnection


# API end-points
API_ENDPOINTS = {
    'uk-1': {
        'name': 'United Kingdom, Manchester',
        'country': 'United Kingdom',
        'host': 'api.z1-man.serverlove.com'
    }
}

# Default API end-point for the base connection class.
DEFAULT_ENDPOINT = 'uk-1'

# Retrieved from http://www.serverlove.com/cloud-server-faqs/api-questions/
STANDARD_DRIVES = {
    '679f5f44-0be7-4745-a658-cccd4334c1aa': {
        'uuid': '679f5f44-0be7-4745-a658-cccd4334c1aa',
        'description': 'CentOS 5.5',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    '5f2e0e29-2937-42b9-b362-d2d07eddbdeb': {
        'uuid': '5f2e0e29-2937-42b9-b362-d2d07eddbdeb',
        'description': 'Ubuntu Linux 10.04',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    '5795b68f-ed26-4639-b41d-c93235062b6b': {
        'uuid': '5795b68f-ed26-4639-b41d-c93235062b6b',
        'description': 'Debian Linux 5',
        'size_gunzipped': '1GB',
        'supports_deployment': True,
    },
    '41993a02-0b22-4e49-bb47-0aa8975217e4': {
        'uuid': '41993a02-0b22-4e49-bb47-0aa8975217e4',
        'description': 'Windows Server 2008 R2 Standard',
        'size_gunzipped': '15GB',
        'supports_deployment': False,
    },
    '85623ca1-9c2a-4398-a771-9a43c347e86b': {
        'uuid': '85623ca1-9c2a-4398-a771-9a43c347e86b',
        'description': 'Windows Web Server 2008 R2',
        'size_gunzipped': '15GB',
        'supports_deployment': False,
    }
}


class ServerLoveConnection(ElasticStackBaseConnection):
    host = API_ENDPOINTS[DEFAULT_ENDPOINT]['host']


class ServerLoveNodeDriver(ElasticStackBaseNodeDriver):
    type = Provider.SERVERLOVE
    api_name = 'serverlove'
    website = 'http://www.serverlove.com/'
    name = 'ServerLove'
    connectionCls = ServerLoveConnection
    features = {'create_node': ['generates_password']}
    _standard_drives = STANDARD_DRIVES
