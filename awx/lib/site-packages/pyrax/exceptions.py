#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Rackspace

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

# Since we use the novaclient package, we need to expose its exception
# classes here.
from novaclient import exceptions as _nova_exceptions
ServerNotFound = _nova_exceptions.NotFound
ServerClientException = _nova_exceptions.ClientException

class PyraxException(Exception):
    pass

class AccessListIDNotFound(PyraxException):
    pass

class AuthenticationFailed(PyraxException):
    pass

class AuthorizationFailure(PyraxException):
    pass

class AuthSystemNotFound(PyraxException):
    pass

class CDNFailed(PyraxException):
    pass

class DNSCallTimedOut(PyraxException):
    pass

class DomainCreationFailed(PyraxException):
    pass

class DomainDeletionFailed(PyraxException):
    pass

class DomainRecordAdditionFailed(PyraxException):
    pass

class DomainRecordDeletionFailed(PyraxException):
    pass

class DomainRecordNotFound(PyraxException):
    pass

class DomainRecordNotUnique(PyraxException):
    pass

class DomainRecordUpdateFailed(PyraxException):
    pass

class DomainUpdateFailed(PyraxException):
    pass

class DuplicateUser(PyraxException):
    pass

class EndpointNotDefined(PyraxException):
    pass

class EndpointNotFound(PyraxException):
    pass

class EnvironmentNotFound(PyraxException):
    pass

class FlavorNotFound(PyraxException):
    pass

class FileNotFound(PyraxException):
    pass

class FolderNotFound(PyraxException):
    pass

class KeyringModuleNotInstalled(PyraxException):
    pass

class KeyringPasswordNotFound(PyraxException):
    pass

class KeyringUsernameMissing(PyraxException):
    pass

class IdentityClassNotDefined(PyraxException):
    pass

class InvalidCDNMetadata(PyraxException):
    pass

class InvalidConfigurationFile(PyraxException):
    pass

class InvalidCredentialFile(PyraxException):
    pass

class InvalidDateTimeString(PyraxException):
    pass

class InvalidDeviceType(PyraxException):
    pass

class InvalidLoadBalancer(PyraxException):
    pass

class InvalidLoadBalancerParameters(PyraxException):
    pass

class InvalidMonitoringCheckDetails(PyraxException):
    pass

class InvalidMonitoringCheckUpdate(PyraxException):
    pass

class InvalidMonitoringMetricsRequest(PyraxException):
    pass

class InvalidMonitoringMetricsResolution(PyraxException):
    pass

class InvalidNodeCondition(PyraxException):
    pass

class InvalidNodeParameters(PyraxException):
    pass

class InvalidPTRRecord(PyraxException):
    pass

class InvalidSessionPersistenceType(PyraxException):
    pass

class InvalidSetting(PyraxException):
    pass

class InvalidSize(PyraxException):
    pass

class InvalidTemporaryURLMethod(PyraxException):
    pass

class InvalidUploadID(PyraxException):
    pass

class InvalidVirtualIPType(PyraxException):
    pass

class InvalidVirtualIPVersion(PyraxException):
    pass

class InvalidVolumeResize(PyraxException):
    pass

class MissingAuthSettings(PyraxException):
    pass

class MissingDNSSettings(PyraxException):
    pass

class MissingHealthMonitorSettings(PyraxException):
    pass

class MissingLoadBalancerParameters(PyraxException):
    pass

class MissingMonitoringCheckDetails(PyraxException):
    pass

class MissingMonitoringCheckGranularity(PyraxException):
    pass

class MissingName(PyraxException):
    pass

class MissingTemporaryURLKey(PyraxException):
    pass

class MonitoringCheckTargetNotSpecified(PyraxException):
    pass

class MonitoringZonesPollMissing(PyraxException):
    pass

class NetworkCIDRInvalid(PyraxException):
    pass

class NetworkCIDRMalformed(PyraxException):
    pass

class NetworkCountExceeded(PyraxException):
    pass

class NetworkInUse(PyraxException):
    pass

class NetworkNotFound(PyraxException):
    pass

class NetworkLabelNotUnique(PyraxException):
    pass

class NoMoreResults(PyraxException):
    pass

class NoReloadError(PyraxException):
    pass

class NoSSLTerminationConfiguration(PyraxException):
    pass

class NoSuchContainer(PyraxException):
    pass

class NoSuchDatabase(PyraxException):
    pass

class NoSuchDatabaseUser(PyraxException):
    pass

class NoSuchObject(PyraxException):
    pass

class NotAuthenticated(PyraxException):
    pass

class NotCDNEnabled(PyraxException):
    pass

class NoTokenLookupException(PyraxException):
    pass

class PasswordChangeFailed(PyraxException):
    pass

class ProtocolMismatch(PyraxException):
    pass

class PTRRecordCreationFailed(PyraxException):
    pass

class PTRRecordDeletionFailed(PyraxException):
    pass

class PTRRecordUpdateFailed(PyraxException):
    pass

class ServiceNotAvailable(PyraxException):
    pass

class SnapshotNotAvailable(PyraxException):
    pass

class TenantNotFound(PyraxException):
    pass

class UnattachedNode(PyraxException):
    pass

class UnattachedVirtualIP(PyraxException):
    pass

class UnicodePathError(PyraxException):
    pass

class UploadFailed(PyraxException):
    pass

class UserNotFound(PyraxException):
    pass

class VolumeAttachmentFailed(PyraxException):
    pass

class VolumeDetachmentFailed(PyraxException):
    pass

class VolumeNotAvailable(PyraxException):
    pass


class AmbiguousEndpoints(PyraxException):
    """Found more than one matching endpoint in Service Catalog."""
    def __init__(self, endpoints=None):
        self.endpoints = endpoints

    def __str__(self):
        return "AmbiguousEndpoints: %s" % repr(self.endpoints)


class ClientException(PyraxException):
    """
    The base exception class for all exceptions this library raises.
    """
    def __init__(self, code, message=None, details=None, request_id=None):
        self.code = code
        self.message = message or self.__class__.message
        self.details = details
        self.request_id = request_id

    def __str__(self):
        formatted_string = "%s (HTTP %s)" % (self.message, self.code)
        if self.request_id:
            formatted_string += " (Request-ID: %s)" % self.request_id

        return formatted_string

class BadRequest(ClientException):
    """
    HTTP 400 - Bad request: you sent some malformed data.
    """
    http_status = 400
    message = "Bad request"


class Unauthorized(ClientException):
    """
    HTTP 401 - Unauthorized: bad credentials.
    """
    http_status = 401
    message = "Unauthorized"


class Forbidden(ClientException):
    """
    HTTP 403 - Forbidden: your credentials don't give you access to this
    resource.
    """
    http_status = 403
    message = "Forbidden"


class NotFound(ClientException):
    """
    HTTP 404 - Not found
    """
    http_status = 404
    message = "Not found"


class NoUniqueMatch(ClientException):
    """
    HTTP 400 - Bad Request
    """
    http_status = 400
    message = "Not Unique"


class OverLimit(ClientException):
    """
    HTTP 413 - Over limit: you're over the API limits for this time period.
    """
    http_status = 413
    message = "Over limit"


# NotImplemented is a python keyword.
class HTTPNotImplemented(ClientException):
    """
    HTTP 501 - Not Implemented: the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"



# In Python 2.4 Exception is old-style and thus doesn't have a __subclasses__()
# so we can do this:
#     _code_map = dict((c.http_status, c)
#                      for c in ClientException.__subclasses__())
#
# Instead, we have to hardcode it:
_code_map = dict((c.http_status, c) for c in [BadRequest, Unauthorized,
        Forbidden, NotFound, OverLimit, HTTPNotImplemented])


def from_response(response, body):
    """
    Return an instance of a ClientException or subclass
    based on an httplib2 response.

    Usage::

        resp, body = http.request(...)
        if resp.status != 200:
            raise exception_from_response(resp, body)
    """
    if isinstance(response, dict):
        status = response.get("status")
    else:
        status = response.status
    cls = _code_map.get(int(status), ClientException)
    request_id = response.get("x-compute-request-id")
    if body:
        message = "n/a"
        details = "n/a"
        if isinstance(body, dict):
            message = body.get("message")
            details = body.get("details")
            if message is details is None:
                error = body[body.keys()[0]]
                if isinstance(error, dict):
                    message = error.get("message", None)
                    details = error.get("details", None)
                else:
                    message = error
                    details = None
        return cls(code=status, message=message, details=details,
                   request_id=request_id)
    else:
        return cls(code=status, request_id=request_id)
