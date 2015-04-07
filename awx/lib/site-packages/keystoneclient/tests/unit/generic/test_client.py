# Copyright 2014 OpenStack Foundation
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

from oslo_serialization import jsonutils

from keystoneclient.generic import client
from keystoneclient.tests.unit import utils

BASE_HOST = 'http://keystone.example.com'
BASE_URL = "%s:5000/" % BASE_HOST
V2_URL = "%sv2.0" % BASE_URL

EXTENSION_NAMESPACE = "http://docs.openstack.org/identity/api/ext/OS-FAKE/v1.0"
EXTENSION_DESCRIBED = {"href": "https://github.com/openstack/identity-api",
                       "rel": "describedby",
                       "type": "text/html"}

EXTENSION_ALIAS_FOO = "OS-FAKE-FOO"
EXTENSION_NAME_FOO = "OpenStack Keystone Fake Extension Foo"
EXTENSION_FOO = {"alias": EXTENSION_ALIAS_FOO,
                 "description": "Fake Foo extension to V2.0 API.",
                 "links": [EXTENSION_DESCRIBED],
                 "name": EXTENSION_NAME_FOO,
                 "namespace": EXTENSION_NAMESPACE,
                 "updated": '2014-01-08T00:00:00Z'}

EXTENSION_ALIAS_BAR = "OS-FAKE-BAR"
EXTENSION_NAME_BAR = "OpenStack Keystone Fake Extension Bar"
EXTENSION_BAR = {"alias": EXTENSION_ALIAS_BAR,
                 "description": "Fake Bar extension to V2.0 API.",
                 "links": [EXTENSION_DESCRIBED],
                 "name": EXTENSION_NAME_BAR,
                 "namespace": EXTENSION_NAMESPACE,
                 "updated": '2014-01-08T00:00:00Z'}


def _create_extension_list(extensions):
    return jsonutils.dumps({'extensions': {'values': extensions}})


EXTENSION_LIST = _create_extension_list([EXTENSION_FOO, EXTENSION_BAR])


class ClientDiscoveryTests(utils.TestCase):

    def test_discover_extensions_v2(self):
        self.requests_mock.get("%s/extensions" % V2_URL, text=EXTENSION_LIST)
        extensions = client.Client().discover_extensions(url=V2_URL)
        self.assertIn(EXTENSION_ALIAS_FOO, extensions)
        self.assertEqual(extensions[EXTENSION_ALIAS_FOO], EXTENSION_NAME_FOO)
        self.assertIn(EXTENSION_ALIAS_BAR, extensions)
        self.assertEqual(extensions[EXTENSION_ALIAS_BAR], EXTENSION_NAME_BAR)
