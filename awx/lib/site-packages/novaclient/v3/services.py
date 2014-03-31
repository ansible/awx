# Copyright 2013 IBM Corp.
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

"""
service interface
"""
from novaclient.v1_1 import services


class Service(services.Service):
    pass


class ServiceManager(services.ServiceManager):
    resource_class = Service

    def _update_body(self, host, binary, disabled_reason=None):
        body = {"service":
                {"host": host,
                 "binary": binary}}
        if disabled_reason is not None:
            body["service"]["disabled_reason"] = disabled_reason
        return body
