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
    "Provider",
    "State",
    "LibcloudLBError",
    "LibcloudLBImmutableError",
]

from libcloud.common.types import LibcloudError


class LibcloudLBError(LibcloudError):
    pass


class LibcloudLBImmutableError(LibcloudLBError):
    pass


class Provider(object):
    RACKSPACE = 'rackspace'
    GOGRID = 'gogrid'
    NINEFOLD = 'ninefold'
    BRIGHTBOX = 'brightbox'
    ELB = 'elb'
    CLOUDSTACK = 'cloudstack'
    GCE = 'gce'

    # Deprecated
    RACKSPACE_US = 'rackspace_us'
    RACKSPACE_UK = 'rackspace_uk'


class State(object):
    """
    Standard states for a loadbalancer

    :cvar RUNNING: loadbalancer is running and ready to use
    :cvar UNKNOWN: loabalancer state is unknown
    """

    RUNNING = 0
    PENDING = 1
    UNKNOWN = 2
    ERROR = 3
    DELETED = 4


class MemberCondition(object):
    """
    Each member of a load balancer can have an associated condition
    which determines its role within the load balancer.
    """
    ENABLED = 0
    DISABLED = 1
    DRAINING = 2
