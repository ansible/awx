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

from novaclient.tests.fixture_data import client
from novaclient.tests.fixture_data import keypairs as data
from novaclient.tests.v1_1 import test_keypairs
from novaclient.v3 import keypairs


class KeypairsTest(test_keypairs.KeypairsTest):

    client_fixture_class = client.V3
    data_fixture_class = data.V3

    def _get_keypair_type(self):
        return keypairs.Keypair

    def _get_keypair_prefix(self):
        return keypairs.KeypairManager.keypair_prefix
