#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
import os

from azure import (
    WindowsAzureError,
    MANAGEMENT_HOST,
    _get_request_body,
    _parse_response,
    _str,
    _update_request_uri_query,
    )
from azure.http import (
    HTTPError,
    HTTPRequest,
    )
from azure.http.httpclient import _HTTPClient
from azure.servicemanagement import (
    AZURE_MANAGEMENT_CERTFILE,
    AZURE_MANAGEMENT_SUBSCRIPTIONID,
    _management_error_handler,
    parse_response_for_async_op,
    X_MS_VERSION,
    )


class _ServiceManagementClient(object):

    def __init__(self, subscription_id=None, cert_file=None,
                 host=MANAGEMENT_HOST, request_session=None):
        self.requestid = None
        self.subscription_id = subscription_id
        self.cert_file = cert_file
        self.host = host
        self.request_session = request_session
        self.x_ms_version = X_MS_VERSION
        self.content_type = 'application/atom+xml;type=entry;charset=utf-8'

        if not self.cert_file and not request_session:
            if AZURE_MANAGEMENT_CERTFILE in os.environ:
                self.cert_file = os.environ[AZURE_MANAGEMENT_CERTFILE]

        if not self.subscription_id:
            if AZURE_MANAGEMENT_SUBSCRIPTIONID in os.environ:
                self.subscription_id = os.environ[
                    AZURE_MANAGEMENT_SUBSCRIPTIONID]

        if not self.request_session:
            if not self.cert_file or not self.subscription_id:
                raise WindowsAzureError(
                    'You need to provide subscription id and certificate file')

        self._httpclient = _HTTPClient(
            service_instance=self, cert_file=self.cert_file,
            request_session=self.request_session)
        self._filter = self._httpclient.perform_request

    def with_filter(self, filter):
        '''Returns a new service which will process requests with the
        specified filter.  Filtering operations can include logging, automatic
        retrying, etc...  The filter is a lambda which receives the HTTPRequest
        and another lambda.  The filter can perform any pre-processing on the
        request, pass it off to the next lambda, and then perform any
        post-processing on the response.'''
        res = type(self)(self.subscription_id, self.cert_file, self.host,
                         self.request_session)
        old_filter = self._filter

        def new_filter(request):
            return filter(request, old_filter)

        res._filter = new_filter
        return res

    def set_proxy(self, host, port, user=None, password=None):
        '''
        Sets the proxy server host and port for the HTTP CONNECT Tunnelling.

        host: Address of the proxy. Ex: '192.168.0.100'
        port: Port of the proxy. Ex: 6000
        user: User for proxy authorization.
        password: Password for proxy authorization.
        '''
        self._httpclient.set_proxy(host, port, user, password)

    def perform_get(self, path, x_ms_version=None):
        '''
        Performs a GET request and returns the response.

        path:
            Path to the resource.
            Ex: '/<subscription-id>/services/hostedservices/<service-name>'
        x_ms_version:
            If specified, this is used for the x-ms-version header.
            Otherwise, self.x_ms_version is used.
        '''
        request = HTTPRequest()
        request.method = 'GET'
        request.host = self.host
        request.path = path
        request.path, request.query = _update_request_uri_query(request)
        request.headers = self._update_management_header(request, x_ms_version)
        response = self._perform_request(request)

        return response

    def perform_put(self, path, body, x_ms_version=None):
        '''
        Performs a PUT request and returns the response.

        path:
            Path to the resource.
            Ex: '/<subscription-id>/services/hostedservices/<service-name>'
        body:
            Body for the PUT request.
        x_ms_version:
            If specified, this is used for the x-ms-version header.
            Otherwise, self.x_ms_version is used.
        '''
        request = HTTPRequest()
        request.method = 'PUT'
        request.host = self.host
        request.path = path
        request.body = _get_request_body(body)
        request.path, request.query = _update_request_uri_query(request)
        request.headers = self._update_management_header(request, x_ms_version)
        response = self._perform_request(request)

        return response

    def perform_post(self, path, body, x_ms_version=None):
        '''
        Performs a POST request and returns the response.

        path:
            Path to the resource.
            Ex: '/<subscription-id>/services/hostedservices/<service-name>'
        body:
            Body for the POST request.
        x_ms_version:
            If specified, this is used for the x-ms-version header.
            Otherwise, self.x_ms_version is used.
        '''
        request = HTTPRequest()
        request.method = 'POST'
        request.host = self.host
        request.path = path
        request.body = _get_request_body(body)
        request.path, request.query = _update_request_uri_query(request)
        request.headers = self._update_management_header(request, x_ms_version)
        response = self._perform_request(request)

        return response

    def perform_delete(self, path, x_ms_version=None):
        '''
        Performs a DELETE request and returns the response.

        path:
            Path to the resource.
            Ex: '/<subscription-id>/services/hostedservices/<service-name>'
        x_ms_version:
            If specified, this is used for the x-ms-version header.
            Otherwise, self.x_ms_version is used.
        '''
        request = HTTPRequest()
        request.method = 'DELETE'
        request.host = self.host
        request.path = path
        request.path, request.query = _update_request_uri_query(request)
        request.headers = self._update_management_header(request, x_ms_version)
        response = self._perform_request(request)

        return response

    #--Helper functions --------------------------------------------------
    def _perform_request(self, request):
        try:
            resp = self._filter(request)
        except HTTPError as ex:
            return _management_error_handler(ex)

        return resp

    def _update_management_header(self, request, x_ms_version):
        ''' Add additional headers for management. '''

        if request.method in ['PUT', 'POST', 'MERGE', 'DELETE']:
            request.headers.append(('Content-Length', str(len(request.body))))

        # append additional headers base on the service
        request.headers.append(('x-ms-version', x_ms_version or self.x_ms_version))

        # if it is not GET or HEAD request, must set content-type.
        if not request.method in ['GET', 'HEAD']:
            for name, _ in request.headers:
                if 'content-type' == name.lower():
                    break
            else:
                request.headers.append(
                    ('Content-Type',
                     self.content_type))

        return request.headers

    def _perform_get(self, path, response_type, x_ms_version=None):
        response = self.perform_get(path, x_ms_version)

        if response_type is not None:
            return _parse_response(response, response_type)

        return response

    def _perform_put(self, path, body, async=False, x_ms_version=None):
        response = self.perform_put(path, body, x_ms_version)

        if async:
            return parse_response_for_async_op(response)

        return None

    def _perform_post(self, path, body, response_type=None, async=False,
                      x_ms_version=None):
        response = self.perform_post(path, body, x_ms_version)

        if response_type is not None:
            return _parse_response(response, response_type)

        if async:
            return parse_response_for_async_op(response)

        return None

    def _perform_delete(self, path, async=False, x_ms_version=None):
        response = self.perform_delete(path, x_ms_version)

        if async:
            return parse_response_for_async_op(response)

        return None

    def _get_path(self, resource, name):
        path = '/' + self.subscription_id + '/' + resource
        if name is not None:
            path += '/' + _str(name)
        return path
