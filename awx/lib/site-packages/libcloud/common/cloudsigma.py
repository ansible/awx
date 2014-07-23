# -*- coding: utf-8 -*-
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

__all__ = [
    'API_ENDPOINTS_1_0',
    'API_ENDPOINTS_2_0',
    'API_VERSIONS',
    'INSTANCE_TYPES'
]

# API end-points
API_ENDPOINTS_1_0 = {
    'zrh': {
        'name': 'Zurich',
        'country': 'Switzerland',
        'host': 'api.zrh.cloudsigma.com'
    },
    'lvs': {
        'name': 'Las Vegas',
        'country': 'United States',
        'host': 'api.lvs.cloudsigma.com'
    }
}

API_ENDPOINTS_2_0 = {
    'zrh': {
        'name': 'Zurich',
        'country': 'Switzerland',
        'host': 'zrh.cloudsigma.com'
    },
    'lvs': {
        'name': 'Las Vegas',
        'country': 'United States',
        'host': 'lvs.cloudsigma.com'
    },
    'wdc': {
        'name': 'Washington DC',
        'country': 'United States',
        'host': 'wdc.cloudsigma.com'
    }

}

DEFAULT_REGION = 'zrh'

# Supported API versions.
API_VERSIONS = [
    '1.0'  # old and deprecated
    '2.0'
]

DEFAULT_API_VERSION = '2.0'

# CloudSigma doesn't specify special instance types.
# Basically for CPU any value between 0.5 GHz and 20.0 GHz should work,
# 500 MB to 32000 MB for ram
# and 1 GB to 1024 GB for hard drive size.
# Plans in this file are based on examples listed on http://www.cloudsigma
# .com/en/pricing/price-schedules
INSTANCE_TYPES = [
    {
        'id': 'micro-regular',
        'name': 'Micro/Regular instance',
        'cpu': 1100,
        'memory': 640,
        'disk': 10 + 3,
        'bandwidth': None,
    },
    {
        'id': 'micro-high-cpu',
        'name': 'Micro/High CPU instance',
        'cpu': 2200,
        'memory': 640,
        'disk': 80,
        'bandwidth': None,
    },
    {
        'id': 'standard-small',
        'name': 'Standard/Small instance',
        'cpu': 1100,
        'memory': 1741,
        'disk': 50,
        'bandwidth': None,
    },
    {
        'id': 'standard-large',
        'name': 'Standard/Large instance',
        'cpu': 4400,
        'memory': 7680,
        'disk': 250,
        'bandwidth': None,
    },
    {
        'id': 'standard-extra-large',
        'name': 'Standard/Extra Large instance',
        'cpu': 8800,
        'memory': 15360,
        'disk': 500,
        'bandwidth': None,
    },
    {
        'id': 'high-memory-extra-large',
        'name': 'High Memory/Extra Large instance',
        'cpu': 7150,
        'memory': 17510,
        'disk': 250,
        'bandwidth': None,
    },
    {
        'id': 'high-memory-double-extra-large',
        'name': 'High Memory/Double Extra Large instance',
        'cpu': 14300,
        'memory': 32768,
        'disk': 500,
        'bandwidth': None,
    },
    {
        'id': 'high-cpu-medium',
        'name': 'High CPU/Medium instance',
        'cpu': 5500,
        'memory': 1741,
        'disk': 150,
        'bandwidth': None,
    },
    {
        'id': 'high-cpu-extra-large',
        'name': 'High CPU/Extra Large instance',
        'cpu': 20000,
        'memory': 7168,
        'disk': 500,
        'bandwidth': None,
    }
]
