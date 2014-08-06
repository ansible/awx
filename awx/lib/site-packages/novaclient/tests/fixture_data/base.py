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
from six.moves.urllib import parse

COMPUTE_URL = 'http://compute.host'


class Fixture(fixtures.Fixture):

    base_url = None

    def __init__(self, compute_url=COMPUTE_URL):
        super(Fixture, self).__init__()
        self.compute_url = compute_url

    def url(self, *args, **kwargs):
        url_args = [self.compute_url]

        if self.base_url:
            url_args.append(self.base_url)

        url = '/'.join(str(a).strip('/') for a in tuple(url_args) + args)

        if kwargs:
            url += '?%s' % parse.urlencode(kwargs, doseq=True)

        return url
