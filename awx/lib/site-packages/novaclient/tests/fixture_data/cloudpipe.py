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

import httpretty

from novaclient.openstack.common import jsonutils
from novaclient.tests.fixture_data import base


class Fixture(base.Fixture):

    base_url = 'os-cloudpipe'

    def setUp(self):
        super(Fixture, self).setUp()

        get_os_cloudpipe = {'cloudpipes': [{'project_id': 1}]}
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_cloudpipe),
                               content_type='application/json')

        instance_id = '9d5824aa-20e6-4b9f-b967-76a699fc51fd'
        post_os_cloudpipe = {'instance_id': instance_id}
        httpretty.register_uri(httpretty.POST, self.url(),
                               body=jsonutils.dumps(post_os_cloudpipe),
                               content_type='application/json',
                               status=202)

        httpretty.register_uri(httpretty.PUT, self.url('configure-project'),
                               content_type='application/json',
                               status=202)
