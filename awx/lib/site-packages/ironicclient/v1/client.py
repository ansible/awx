# -*- coding: utf-8 -*-
#
# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from ironicclient.common import http
from ironicclient.v1 import chassis
from ironicclient.v1 import driver
from ironicclient.v1 import node
from ironicclient.v1 import port


# NOTE(deva): Record the latest version that this client was tested with.
#             We still have a lot of work to do in the client to implement
#             microversion support in the client properly! See
#             http://specs.openstack.org/openstack/ironic-specs/specs/kilo/api-microversions.html # noqa
#             for full details.
DEFAULT_VER = '1.6'


class Client(object):
    """Client for the Ironic v1 API.

    :param string endpoint: A user-supplied endpoint URL for the ironic
                            service.
    :param function token: Provides token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    """

    def __init__(self, *args, **kwargs):
        """Initialize a new client for the Ironic v1 API."""
        # set the default API version header string, if none specified
        if not kwargs.get('os_ironic_api_version'):
            kwargs['os_ironic_api_version'] = DEFAULT_VER
        self.http_client = http._construct_http_client(*args, **kwargs)
        self.chassis = chassis.ChassisManager(self.http_client)
        self.node = node.NodeManager(self.http_client)
        self.port = port.PortManager(self.http_client)
        self.driver = driver.DriverManager(self.http_client)
