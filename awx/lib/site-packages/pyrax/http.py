# Copyright (c)2014 Rackspace US, Inc.

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
"""
Wrapper around the requests library. Used for making all HTTP calls.
"""

import logging
import json
import requests

import pyrax
import pyrax.exceptions as exc


req_methods = {
    "HEAD": requests.head,
    "GET": requests.get,
    "POST": requests.post,
    "PUT": requests.put,
    "DELETE": requests.delete,
    "PATCH": requests.patch,
    }

# NOTE: FIX THIS!!!
verify_ssl = False


def request(method, uri, *args, **kwargs):
    """
    Handles all the common functionality required for API calls. Returns
    the resulting response object.

    Formats the request into a dict representing the headers
    and body that will be used to make the API call.
    """
    req_method = req_methods[method.upper()]
    raise_exception = kwargs.pop("raise_exception", True)
    kwargs["headers"] = kwargs.get("headers", {})
    http_log_req(method, uri, args, kwargs)
    data = None
    if "data" in kwargs:
        # The 'data' kwarg is used when you don't want json encoding.
        data = kwargs.pop("data")
    elif "body" in kwargs:
        if "Content-Type" not in kwargs["headers"]:
            kwargs["headers"]["Content-Type"] = "application/json"
        data = json.dumps(kwargs.pop("body"))
    if data:
        resp = req_method(uri, data=data, **kwargs)
    else:
        resp = req_method(uri, **kwargs)
    try:
        body = resp.json()
    except ValueError:
        # No JSON in response
        body = resp.content
    http_log_resp(resp, body)
    if resp.status_code >= 400 and raise_exception:
        raise exc.from_response(resp, body)
    return resp, body


def http_log_req(method, uri, args, kwargs):
    """
    When pyrax.get_http_debug() is True, outputs the equivalent `curl`
    command for the API request being made.
    """
    if not pyrax.get_http_debug():
        return
    string_parts = ["curl -i -X %s" % method]
    for element in args:
        string_parts.append("%s" % element)
    for element in kwargs["headers"]:
        header = "-H '%s: %s'" % (element, kwargs["headers"][element])
        string_parts.append(header)
    string_parts.append(uri)
    log = logging.getLogger("pyrax")
    log.debug("\nREQ: %s\n" % " ".join(string_parts))
    if "body" in kwargs:
        pyrax._logger.debug("REQ BODY: %s\n" % (kwargs["body"]))
    if "data" in kwargs:
        pyrax._logger.debug("REQ DATA: %s\n" % (kwargs["data"]))


def http_log_resp(resp, body):
    """
    When pyrax.get_http_debug() is True, outputs the response received
    from the API request.
    """
    if not pyrax.get_http_debug():
        return
    log = logging.getLogger("pyrax")
    log.debug("RESP: %s\n%s", resp, resp.headers)
    if body:
        log.debug("RESP BODY: %s", body)
