# Copyright 2012 Rackspace
# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
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

import novaclient.auth_plugin

class RackspaceAuthPlugin(novaclient.auth_plugin.BaseAuthPlugin):
    '''The RackspaceAuthPlugin simply provides authenticate, no extra options'''
    def authenticate(self, cls, auth_url):
        _authenticate(cls, auth_url)


def auth_url_us():
    """Return the Rackspace Cloud US Auth URL"""
    return "https://identity.api.rackspacecloud.com/v2.0/"


def auth_url_uk():
    """Return the Rackspace Cloud UK Auth URL"""
    return "https://lon.identity.api.rackspacecloud.com/v2.0/"


def _authenticate(cls, auth_url):
    """Authenticate against the Rackspace auth service."""
    body = {"auth": {
        "RAX-KSKEY:apiKeyCredentials": {
            "username": cls.user,
            "apiKey": cls.password},
        }}
    return cls._authenticate(auth_url, body)


def authenticate_us(cls,
                    auth_url=auth_url_us()):
    """Authenticate against the Rackspace US auth service."""
    return _authenticate(cls, auth_url)

def authenticate_uk(cls,
                    auth_url=auth_url_uk()):
    """Authenticate against the Rackspace UK auth service."""
    return _authenticate(cls, auth_url)
