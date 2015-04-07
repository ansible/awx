#    Copyright 2011 OpenStack Foundation
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


class UnsupportedVersion(Exception):
    """Indicates that the user is trying to use an unsupported
    version of the API.
    """
    pass


class CommandError(Exception):
    pass


class AuthorizationFailure(Exception):
    pass


class NoUniqueMatch(Exception):
    pass


class NoTokenLookupException(Exception):
    """This form of authentication does not support looking up
       endpoints from an existing token.
    """
    pass


class EndpointNotFound(Exception):
    """Could not find Service or Region in Service Catalog."""
    pass


class AuthUrlNotGiven(EndpointNotFound):
    """The auth url was not given."""
    pass


class ServiceUrlNotGiven(EndpointNotFound):
    """The service url was not given."""
    pass


class ResponseFormatError(Exception):
    """Could not parse the response format."""
    pass


class AmbiguousEndpoints(Exception):
    """Found more than one matching endpoint in Service Catalog."""
    def __init__(self, endpoints=None):
        self.endpoints = endpoints

    def __str__(self):
        return "AmbiguousEndpoints: %s" % repr(self.endpoints)


class ClientException(Exception):
    """The base exception class for all exceptions this library raises."""
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
    """HTTP 400 - Bad request: you sent some malformed data."""
    http_status = 400
    message = "Bad request"


class Unauthorized(ClientException):
    """HTTP 401 - Unauthorized: bad credentials."""
    http_status = 401
    message = "Unauthorized"


class Forbidden(ClientException):
    """HTTP 403 - Forbidden: your don't have access to this resource."""
    http_status = 403
    message = "Forbidden"


class NotFound(ClientException):
    """HTTP 404 - Not found."""
    http_status = 404
    message = "Not found"


class Conflict(ClientException):
    """HTTP 409 - Conflict."""
    http_status = 409
    message = "Conflict"


class OverLimit(ClientException):
    """HTTP 413
    - Over limit: you're over the API limits for this time period.
    """
    http_status = 413
    message = "Over limit"


# NotImplemented is a python keyword.
class HTTPNotImplemented(ClientException):
    """HTTP 501
    - Not Implemented: the server does not support this operation.
    """
    http_status = 501
    message = "Not Implemented"


class UnprocessableEntity(ClientException):
    """HTTP 422 - Unprocessable Entity: The request cannot be processed."""
    http_status = 422
    message = "Unprocessable Entity"


# In Python 2.4 Exception is old-style and thus doesn't have a __subclasses__()
# so we can do this:
#     _code_map = dict((c.http_status, c)
#                      for c in ClientException.__subclasses__())
#
# Instead, we have to hardcode it:
_code_map = dict((c.http_status, c) for c in [BadRequest, Unauthorized,
                                              Forbidden, NotFound, Conflict,
                                              OverLimit, HTTPNotImplemented,
                                              UnprocessableEntity])


def from_response(response, body):
    """Return an instance of an ClientException based on a request's response.

    Usage::

        resp, body = http.request(...)
        if resp.status != 200:
            raise exception_from_response(resp, body)
    """
    cls = _code_map.get(response.status, ClientException)
    if body:
        message = "n/a"
        details = "n/a"
        if hasattr(body, 'keys'):
            error = body[body.keys()[0]]
            message = error.get('message', None)
            details = error.get('details', None)
        return cls(code=response.status, message=message, details=details)
    else:
        request_id = response.get('x-compute-request-id')
        return cls(code=response.status, request_id=request_id)
