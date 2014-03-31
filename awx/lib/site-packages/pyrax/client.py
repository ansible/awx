# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
# Copyright 2011 Piston Cloud Computing, Inc.
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
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import json
import logging
import requests
import time
import urllib
import urlparse

import pyrax
import pyrax.exceptions as exc


class BaseClient(object):
    """
    The base class for all pyrax clients.
    """
    # This will get set by pyrax when the service is started.
    user_agent = None
    # Each client subclass should set their own name.
    name = "base"

    def __init__(self, region_name=None, endpoint_type="publicURL",
            management_url=None, service_name=None, timings=False,
            verify_ssl=True, http_log_debug=False, timeout=None):
        self.version = "v1.1"
        self.region_name = region_name
        self.endpoint_type = endpoint_type
        self.service_name = service_name
        self.management_url = management_url
        self.timings = timings
        self.verify_ssl = verify_ssl
        self.http_log_debug = http_log_debug
        self.timeout = timeout
        self.times = []  # [("item", starttime, endtime), ...]

        self._manager = None
        # Hook method for subclasses to create their manager instance
        # without having to override __init__().
        self._configure_manager()


    def _configure_manager(self):
        """
        This must be overridden in base classes to create
        the required manager class and configure it as needed.
        """
        raise NotImplementedError


    # The next 6 methods are simple pass-through to the manager.
    def list(self, limit=None, marker=None):
        """
        Returns a list of resource objects. Pagination is supported through the
        optional 'marker' and 'limit' parameters.
        """
        return self._manager.list(limit=limit, marker=marker)


    def get(self, item):
        """Gets a specific resource."""
        return self._manager.get(item)


    def create(self, *args, **kwargs):
        """Creates a new resource."""
        return self._manager.create(*args, **kwargs)


    def delete(self, item):
        """Deletes a specific resource."""
        return self._manager.delete(item)


    def find(self, **kwargs):
        """
        Finds a single item with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        return self._manager.find(**kwargs)


    def findall(self, **kwargs):
        """
        Finds all items with attributes matching ``**kwargs``.

        This isn't very efficient: it loads the entire list then filters on
        the Python side.
        """
        return self._manager.findall(**kwargs)


    def unauthenticate(self):
        """Clears all of our authentication information."""
        pyrax.identity.unauthenticate()


    def get_timings(self):
        """Returns a list of all execution timings."""
        return self.times


    def reset_timings(self):
        """Clears the timing history."""
        self.times = []


    def get_limits(self):
        """
        Returns a dict with the resource and rate limits for the account.
        """
        resp, resp_body = self.method_get("/limits")
        return resp_body


    def _add_custom_headers(self, dct):
        """
        Clients for some services must add headers that are required for that
        service. This is a hook method to allow for such customization.

        If a client needs to add a special header, the 'dct' parameter is a
        dictionary of headers. Add the header(s) and their values as key/value
        pairs to the 'dct'.
        """
        pass


    def request(self, uri, method, *args, **kwargs):
        """
        Formats the request into a dict representing the headers
        and body that will be used to make the API call.
        """
        if self.timeout:
            kwargs["timeout"] = self.timeout
        kwargs["verify"] = self.verify_ssl
        kwargs.setdefault("headers", kwargs.get("headers", {}))
        kwargs["headers"]["User-Agent"] = self.user_agent
        kwargs["headers"]["Accept"] = "application/json"
        # Allow subclasses to add their own headers
        self._add_custom_headers(kwargs["headers"])
        resp, body = pyrax.http.request(method, uri, *args, **kwargs)
        if resp.status_code >= 400:
            raise exc.from_response(resp, body)
        return resp, body


    def _time_request(self, uri, method, **kwargs):
        """Wraps the request call and records the elapsed time."""
        start_time = time.time()
        resp, body = self.request(uri, method, **kwargs)
        self.times.append(("%s %s" % (method, uri),
                start_time, time.time()))
        return resp, body


    def _api_request(self, uri, method, **kwargs):
        """
        Manages the request by adding any auth information, and retries
        the request after authenticating if the initial request returned
        and Unauthorized exception.
        """
        id_svc = pyrax.identity
        if not all((self.management_url, id_svc.token, id_svc.tenant_id)):
            id_svc.authenticate()

        if not self.management_url:
            # We've authenticated but no management_url has been set. This
            # indicates that the service is not available.
            raise exc.ServiceNotAvailable("The '%s' service is not available."
                    % self)
        if uri.startswith("http"):
            parsed = list(urlparse.urlparse(uri))
            for pos, item in enumerate(parsed):
                if pos < 2:
                    # Don't escape the scheme or netloc
                    continue
                parsed[pos] = urllib.quote(parsed[pos], safe="/.?&=,")
            safe_uri = urlparse.urlunparse(parsed)
        else:
            safe_uri = "%s%s" % (self.management_url,
                    urllib.quote(uri, safe="/.?&=,"))
        # Perform the request once. If we get a 401 back then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            kwargs.setdefault("headers", {})["X-Auth-Token"] = id_svc.token
            if id_svc.tenant_id:
                kwargs["headers"]["X-Auth-Project-Id"] = id_svc.tenant_id
            resp, body = self._time_request(safe_uri, method, **kwargs)
            return resp, body
        except exc.Unauthorized as ex:
            try:
                id_svc.authenticate()
                kwargs["headers"]["X-Auth-Token"] = id_svc.token
                resp, body = self._time_request(safe_uri, method, **kwargs)
                return resp, body
            except exc.Unauthorized:
                raise ex


    def method_head(self, uri, **kwargs):
        """Method used to make HEAD requests."""
        return self._api_request(uri, "HEAD", **kwargs)


    def method_get(self, uri, **kwargs):
        """Method used to make GET requests."""
        return self._api_request(uri, "GET", **kwargs)


    def method_post(self, uri, **kwargs):
        """Method used to make POST requests."""
        return self._api_request(uri, "POST", **kwargs)


    def method_put(self, uri, **kwargs):
        """Method used to make PUT requests."""
        return self._api_request(uri, "PUT", **kwargs)


    def method_delete(self, uri, **kwargs):
        """Method used to make DELETE requests."""
        return self._api_request(uri, "DELETE", **kwargs)


    def method_patch(self, uri, **kwargs):
        """Method used to make PATCH requests."""
        return self._api_request(uri, "PATCH", **kwargs)


    def authenticate(self):
        """
        Handles all aspects of authentication against the cloud provider.
        Currently this has only been tested with Rackspace auth; if you wish
        to use this library with a different OpenStack provider, you may have
        to modify this method. Please post your findings on GitHub so that
        others can benefit.
        """
        return pyrax.identity.authenticate()


    @property
    def projectid(self):
        """
        The older parts of this code used 'projectid'; this wraps that
        reference.
        """
        return pyrax.identity.tenant_id
