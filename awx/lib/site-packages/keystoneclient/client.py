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

from keystoneclient import discover
from keystoneclient import httpclient
from keystoneclient import session as client_session


# Using client.HTTPClient is deprecated. Use httpclient.HTTPClient instead.
HTTPClient = httpclient.HTTPClient


def Client(version=None, unstable=False, session=None, **kwargs):
    """Factory function to create a new identity service client.

    The returned client will be either a V3 or V2 client. Check the version
    using the :py:attr:`~keystoneclient.v3.client.Client.version` property or
    the instance's class (with instanceof).

    :param tuple version: The required version of the identity API. If
                          specified the client will be selected such that the
                          major version is equivalent and an endpoint provides
                          at least the specified minor version. For example to
                          specify the 3.1 API use ``(3, 1)``.
    :param bool unstable: Accept endpoints not marked as 'stable'. (optional)
    :param session: A session object to be used for communication. If one is
                    not provided it will be constructed from the provided
                    kwargs. (optional)
    :type session: keystoneclient.session.Session
    :param kwargs: Additional arguments are passed through to the client
                   that is being created.
    :returns: New keystone client object.
    :rtype: :py:class:`keystoneclient.v3.client.Client` or
            :py:class:`keystoneclient.v2_0.client.Client`
    :raises keystoneclient.exceptions.DiscoveryFailure: if the server's
                                                        response is invalid.
    :raises keystoneclient.exceptions.VersionNotAvailable: if a suitable client
                                                           cannot be found.
    """
    if not session:
        session = client_session.Session.construct(kwargs)

    d = discover.Discover(session=session, **kwargs)
    return d.create_client(version=version, unstable=unstable)
