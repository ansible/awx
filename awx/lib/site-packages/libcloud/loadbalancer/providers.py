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

from libcloud.utils.misc import get_driver as get_provider_driver
from libcloud.utils.misc import set_driver as set_provider_driver
from libcloud.loadbalancer.types import Provider

__all__ = [
    "Provider",
    "DRIVERS",
    "get_driver",
]

DRIVERS = {
    Provider.RACKSPACE:
    ('libcloud.loadbalancer.drivers.rackspace', 'RackspaceLBDriver'),
    Provider.GOGRID:
    ('libcloud.loadbalancer.drivers.gogrid', 'GoGridLBDriver'),
    Provider.NINEFOLD:
    ('libcloud.loadbalancer.drivers.ninefold', 'NinefoldLBDriver'),
    Provider.BRIGHTBOX:
    ('libcloud.loadbalancer.drivers.brightbox', 'BrightboxLBDriver'),
    Provider.ELB:
    ('libcloud.loadbalancer.drivers.elb', 'ElasticLBDriver'),
    Provider.CLOUDSTACK:
    ('libcloud.loadbalancer.drivers.cloudstack', 'CloudStackLBDriver'),
    Provider.GCE:
    ('libcloud.loadbalancer.drivers.gce', 'GCELBDriver'),

    # Deprecated
    Provider.RACKSPACE_US:
    ('libcloud.loadbalancer.drivers.rackspace', 'RackspaceLBDriver'),
    Provider.RACKSPACE_UK:
    ('libcloud.loadbalancer.drivers.rackspace', 'RackspaceUKLBDriver'),
}


def get_driver(provider):
    return get_provider_driver(DRIVERS, provider)


def set_driver(provider, module, klass):
    return set_provider_driver(DRIVERS, provider, module, klass)
