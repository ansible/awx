#
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

# NOTE(akurilin): This module is left for backward compatibility. Feel free to
#                 remove it, when openstack project will use correct way to
#                 obtain novaclient object.
#   Known problems:
#    * python-openstackclient -
#        https://bugs.launchpad.net/python-openstackclient/+bug/1418024
#    * neutron - https://bugs.launchpad.net/neutron/+bug/1418017


import sys
import warnings

from novaclient import v2

warnings.warn("Module novaclient.v1_1 is deprecated (taken as a basis for "
              "novaclient.v2). "
              "The preferable way to get client class or object you can find "
              "in novaclient.client module.")


class MovedModule(object):
    def __init__(self, new_module):
        self.new_module = new_module

    def __getattr__(self, attr):
        return getattr(self.new_module, attr)

sys.modules["novaclient.v1_1"] = MovedModule(v2)
