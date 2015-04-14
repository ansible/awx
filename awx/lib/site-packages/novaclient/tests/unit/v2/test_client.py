# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import uuid

from keystoneclient import session

from novaclient.tests.unit import utils
from novaclient.v2 import client


class ClientTest(utils.TestCase):

    def test_adapter_properties(self):
        # sample of properties, there are many more
        user_agent = uuid.uuid4().hex
        endpoint_override = uuid.uuid4().hex

        s = session.Session()
        c = client.Client(session=s,
                          user_agent=user_agent,
                          endpoint_override=endpoint_override)

        self.assertEqual(user_agent, c.client.user_agent)
        self.assertEqual(endpoint_override, c.client.endpoint_override)

    def test_passing_interface(self):
        endpoint_type = uuid.uuid4().hex
        interface = uuid.uuid4().hex

        s = session.Session()
        c = client.Client(session=s,
                          interface=interface,
                          endpoint_type=endpoint_type)

        self.assertEqual(interface, c.client.interface)
