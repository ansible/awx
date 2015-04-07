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

import fixtures

IDENTITY_URL = 'http://identityserver:5000/v2.0'
VOLUME_URL = 'http://volume.host'


class Fixture(fixtures.Fixture):

    base_url = None
    json_headers = {'Content-Type': 'application/json'}

    def __init__(self, requests,
                 volume_url=VOLUME_URL,
                 identity_url=IDENTITY_URL):
        super(Fixture, self).__init__()
        self.requests = requests
        self.volume_url = volume_url
        self.identity_url = identity_url

    def url(self, *args):
        url_args = [self.volume_url]

        if self.base_url:
            url_args.append(self.base_url)

        return '/'.join(str(a).strip('/') for a in tuple(url_args) + args)
