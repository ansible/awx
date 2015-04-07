# Copyright 2011 OpenStack Foundation
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
from six.moves.urllib import parse

from troveclient.openstack.common.apiclient import exceptions


def check_for_exceptions(resp, body, url):
    if resp.status_code in (400, 422, 500):
        raise exceptions.from_response(resp, body, url)


def append_query_strings(url, **query_strings):
    if not query_strings:
        return url
    query = '&'.join('{0}={1}'.format(key, val)
                     for key, val in query_strings.items() if val)
    return url + ('?' + query if query else "")


def quote_user_host(user, host):
    quoted = ''
    if host:
        quoted = parse.quote("%s@%s" % (user, host))
    else:
        quoted = parse.quote("%s" % user)
    return quoted.replace('.', '%2e')


class Paginated(object):
    """Pretends to be a list if you iterate over it, but also keeps a
       next property you can use to get the next page of data.
    """

    def __init__(self, items=[], next_marker=None, links=[]):
        self.items = items
        self.next = next_marker
        self.links = links

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return self.items.__iter__()

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    def __delitem__(self, key):
        del self.items[key]

    def __reversed__(self):
        return reversed(self.items)

    def __contains__(self, needle):
        return needle in self.items
