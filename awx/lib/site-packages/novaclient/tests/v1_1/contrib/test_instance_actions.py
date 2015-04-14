# Copyright 2013 Rackspace Hosting
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

from novaclient import extension
from novaclient.tests import utils
from novaclient.tests.v1_1.contrib import fakes
from novaclient.v1_1.contrib import instance_action


extensions = [
    extension.Extension(instance_action.__name__.split(".")[-1],
                        instance_action),
]
cs = fakes.FakeClient(extensions=extensions)


class InstanceActionExtensionTests(utils.TestCase):
    def test_list_instance_actions(self):
        server_uuid = '1234'
        cs.instance_action.list(server_uuid)
        cs.assert_called('GET', '/servers/%s/os-instance-actions' %
                server_uuid)

    def test_get_instance_action(self):
        server_uuid = '1234'
        request_id = 'req-abcde12345'
        cs.instance_action.get(server_uuid, request_id)
        cs.assert_called('GET', '/servers/%s/os-instance-actions/%s' %
                (server_uuid, request_id))
