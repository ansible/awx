# Copyright 2012 OpenStack Foundation
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

"""
Virtual Interfaces (1.1 extension).
"""

from novaclient import base


class VirtualInterface(base.Resource):
    def __repr__(self):
        pass


class VirtualInterfaceManager(base.ManagerWithFind):
    resource_class = VirtualInterface

    def list(self, instance_id):
        return self._list('/servers/%s/os-virtual-interfaces' % instance_id,
                          'virtual_interfaces')
