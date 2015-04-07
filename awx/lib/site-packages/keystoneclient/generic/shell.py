# Copyright 2010 OpenStack Foundation
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

import six

from keystoneclient.generic import client
from keystoneclient.i18n import _
from keystoneclient import utils


CLIENT_CLASS = client.Client


@utils.unauthenticated
def do_discover(cs, args):
    """Discover Keystone servers, supported API versions and extensions.
    """
    if cs.endpoint:
        versions = cs.discover(cs.endpoint)
    elif cs.auth_url:
        versions = cs.discover(cs.auth_url)
    else:
        versions = cs.discover()
    if versions:
        if 'message' in versions:
            print(versions['message'])
        for key, version in six.iteritems(versions):
            if key != 'message':
                print(_("    - supports version %(id)s (%(status)s) here "
                        "%(url)s") %
                      version)
                extensions = cs.discover_extensions(version['url'])
                if extensions:
                    for key, extension in six.iteritems(extensions):
                        if key != 'message':
                            print(_("        - and %(key)s: %(extension)s") %
                                  {'key': key, 'extension': extension})
    else:
        print(_("No Keystone-compatible endpoint found"))
