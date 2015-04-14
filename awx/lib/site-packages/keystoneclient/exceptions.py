# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 Nebula, Inc.
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
"""
Exception definitions.

.. py:exception:: AuthorizationFailure

.. py:exception:: ClientException

.. py:exception:: HttpError

.. py:exception:: ValidationError

.. py:exception:: Unauthorized

"""

from keystoneclient.i18n import _
from keystoneclient.openstack.common.apiclient.exceptions import *  # noqa

# NOTE(akurilin): This alias should be left here to support backwards
# compatibility until we are sure that usage of these exceptions in
# projects is correct.
ConnectionError = ConnectionRefused
HTTPNotImplemented = HttpNotImplemented
Timeout = RequestTimeout
HTTPError = HttpError


class CertificateConfigError(Exception):
    """Error reading the certificate."""
    def __init__(self, output):
        self.output = output
        msg = _('Unable to load certificate.')
        super(CertificateConfigError, self).__init__(msg)


class CMSError(Exception):
    """Error reading the certificate."""
    def __init__(self, output):
        self.output = output
        msg = _('Unable to sign or verify data.')
        super(CMSError, self).__init__(msg)


class EmptyCatalog(EndpointNotFound):
    """The service catalog is empty."""
    pass


class SSLError(ConnectionRefused):
    """An SSL error occurred."""


class DiscoveryFailure(ClientException):
    """Discovery of client versions failed."""


class VersionNotAvailable(DiscoveryFailure):
    """Discovery failed as the version you requested is not available."""


class MethodNotImplemented(ClientException):
    """Method not implemented by the keystoneclient API."""


class MissingAuthPlugin(ClientException):
    """An authenticated request is required but no plugin available."""


class NoMatchingPlugin(ClientException):
    """There were no auth plugins that could be created from the parameters
    provided.

    :param str name: The name of the plugin that was attempted to load.

    .. py:attribute:: name

        The name of the plugin that was attempted to load.
    """

    def __init__(self, name):
        self.name = name
        msg = _('The plugin %s could not be found') % name
        super(NoMatchingPlugin, self).__init__(msg)


class InvalidResponse(ClientException):
    """The response from the server is not valid for this request."""

    def __init__(self, response):
        super(InvalidResponse, self).__init__()
        self.response = response
