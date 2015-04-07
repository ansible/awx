# Copyright 2012 OpenStack Foundation
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011,2012 Akira YOSHIYAMA <akirayoshiyama@gmail.com>
# All Rights Reserved.
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

# This source code is based ./auth_token.py and ./ec2_token.py.
# See them for their copyright.

"""
S3 TOKEN MIDDLEWARE

This WSGI component:

* Get a request from the swift3 middleware with an S3 Authorization
  access key.
* Validate s3 token in Keystone.
* Transform the account name to AUTH_%(tenant_name).

"""

import logging

from oslo_serialization import jsonutils
import requests
import six
from six.moves import urllib
import webob


PROTOCOL_NAME = 'S3 Token Authentication'


# TODO(kun): remove it after oslo merge this.
def split_path(path, minsegs=1, maxsegs=None, rest_with_last=False):
    """Validate and split the given HTTP request path.

    **Examples**::

        ['a'] = split_path('/a')
        ['a', None] = split_path('/a', 1, 2)
        ['a', 'c'] = split_path('/a/c', 1, 2)
        ['a', 'c', 'o/r'] = split_path('/a/c/o/r', 1, 3, True)

    :param path: HTTP Request path to be split
    :param minsegs: Minimum number of segments to be extracted
    :param maxsegs: Maximum number of segments to be extracted
    :param rest_with_last: If True, trailing data will be returned as part
                           of last segment.  If False, and there is
                           trailing data, raises ValueError.
    :returns: list of segments with a length of maxsegs (non-existent
              segments will return as None)
    :raises: ValueError if given an invalid path
    """
    if not maxsegs:
        maxsegs = minsegs
    if minsegs > maxsegs:
        raise ValueError('minsegs > maxsegs: %d > %d' % (minsegs, maxsegs))
    if rest_with_last:
        segs = path.split('/', maxsegs)
        minsegs += 1
        maxsegs += 1
        count = len(segs)
        if (segs[0] or count < minsegs or count > maxsegs or
                '' in segs[1:minsegs]):
            raise ValueError('Invalid path: %s' % urllib.parse.quote(path))
    else:
        minsegs += 1
        maxsegs += 1
        segs = path.split('/', maxsegs)
        count = len(segs)
        if (segs[0] or count < minsegs or count > maxsegs + 1 or
                '' in segs[1:minsegs] or
                (count == maxsegs + 1 and segs[maxsegs])):
            raise ValueError('Invalid path: %s' % urllib.parse.quote(path))
    segs = segs[1:maxsegs]
    segs.extend([None] * (maxsegs - 1 - len(segs)))
    return segs


class ServiceError(Exception):
    pass


class S3Token(object):
    """Auth Middleware that handles S3 authenticating client calls."""

    def __init__(self, app, conf):
        """Common initialization code."""
        self.app = app
        self.logger = logging.getLogger(conf.get('log_name', __name__))
        self.logger.debug('Starting the %s component', PROTOCOL_NAME)
        self.logger.warning(
            'This middleware module is deprecated as of v0.11.0 in favor of '
            'keystonemiddleware.s3_token - please update your WSGI pipeline '
            'to reference the new middleware package.')
        self.reseller_prefix = conf.get('reseller_prefix', 'AUTH_')
        # where to find the auth service (we use this to validate tokens)

        auth_host = conf.get('auth_host')
        auth_port = int(conf.get('auth_port', 35357))
        auth_protocol = conf.get('auth_protocol', 'https')

        self.request_uri = '%s://%s:%s' % (auth_protocol, auth_host, auth_port)

        # SSL
        insecure = conf.get('insecure', False)
        cert_file = conf.get('certfile')
        key_file = conf.get('keyfile')

        if insecure:
            self.verify = False
        elif cert_file and key_file:
            self.verify = (cert_file, key_file)
        elif cert_file:
            self.verify = cert_file
        else:
            self.verify = None

    def deny_request(self, code):
        error_table = {
            'AccessDenied': (401, 'Access denied'),
            'InvalidURI': (400, 'Could not parse the specified URI'),
        }
        resp = webob.Response(content_type='text/xml')
        resp.status = error_table[code][0]
        error_msg = ('<?xml version="1.0" encoding="UTF-8"?>\r\n'
                     '<Error>\r\n  <Code>%s</Code>\r\n  '
                     '<Message>%s</Message>\r\n</Error>\r\n' %
                     (code, error_table[code][1]))
        if six.PY3:
            error_msg = error_msg.encode()
        resp.body = error_msg
        return resp

    def _json_request(self, creds_json):
        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post('%s/v2.0/s3tokens' % self.request_uri,
                                     headers=headers, data=creds_json,
                                     verify=self.verify)
        except requests.exceptions.RequestException as e:
            self.logger.info('HTTP connection exception: %s', e)
            resp = self.deny_request('InvalidURI')
            raise ServiceError(resp)

        if response.status_code < 200 or response.status_code >= 300:
            self.logger.debug('Keystone reply error: status=%s reason=%s',
                              response.status_code, response.reason)
            resp = self.deny_request('AccessDenied')
            raise ServiceError(resp)

        return response

    def __call__(self, environ, start_response):
        """Handle incoming request. authenticate and send downstream."""
        req = webob.Request(environ)
        self.logger.debug('Calling S3Token middleware.')

        try:
            parts = split_path(req.path, 1, 4, True)
            version, account, container, obj = parts
        except ValueError:
            msg = 'Not a path query, skipping.'
            self.logger.debug(msg)
            return self.app(environ, start_response)

        # Read request signature and access id.
        if 'Authorization' not in req.headers:
            msg = 'No Authorization header. skipping.'
            self.logger.debug(msg)
            return self.app(environ, start_response)

        token = req.headers.get('X-Auth-Token',
                                req.headers.get('X-Storage-Token'))
        if not token:
            msg = 'You did not specify an auth or a storage token. skipping.'
            self.logger.debug(msg)
            return self.app(environ, start_response)

        auth_header = req.headers['Authorization']
        try:
            access, signature = auth_header.split(' ')[-1].rsplit(':', 1)
        except ValueError:
            msg = 'You have an invalid Authorization header: %s'
            self.logger.debug(msg, auth_header)
            return self.deny_request('InvalidURI')(environ, start_response)

        # NOTE(chmou): This is to handle the special case with nova
        # when we have the option s3_affix_tenant. We will force it to
        # connect to another account than the one
        # authenticated. Before people start getting worried about
        # security, I should point that we are connecting with
        # username/token specified by the user but instead of
        # connecting to its own account we will force it to go to an
        # another account. In a normal scenario if that user don't
        # have the reseller right it will just fail but since the
        # reseller account can connect to every account it is allowed
        # by the swift_auth middleware.
        force_tenant = None
        if ':' in access:
            access, force_tenant = access.split(':')

        # Authenticate request.
        creds = {'credentials': {'access': access,
                                 'token': token,
                                 'signature': signature}}
        creds_json = jsonutils.dumps(creds)
        self.logger.debug('Connecting to Keystone sending this JSON: %s',
                          creds_json)
        # NOTE(vish): We could save a call to keystone by having
        #             keystone return token, tenant, user, and roles
        #             from this call.
        #
        # NOTE(chmou): We still have the same problem we would need to
        #              change token_auth to detect if we already
        #              identified and not doing a second query and just
        #              pass it through to swiftauth in this case.
        try:
            resp = self._json_request(creds_json)
        except ServiceError as e:
            resp = e.args[0]
            msg = 'Received error, exiting middleware with error: %s'
            self.logger.debug(msg, resp.status_code)
            return resp(environ, start_response)

        self.logger.debug('Keystone Reply: Status: %d, Output: %s',
                          resp.status_code, resp.content)

        try:
            identity_info = resp.json()
            token_id = str(identity_info['access']['token']['id'])
            tenant = identity_info['access']['token']['tenant']
        except (ValueError, KeyError):
            error = 'Error on keystone reply: %d %s'
            self.logger.debug(error, resp.status_code, resp.content)
            return self.deny_request('InvalidURI')(environ, start_response)

        req.headers['X-Auth-Token'] = token_id
        tenant_to_connect = force_tenant or tenant['id']
        self.logger.debug('Connecting with tenant: %s', tenant_to_connect)
        new_tenant_name = '%s%s' % (self.reseller_prefix, tenant_to_connect)
        environ['PATH_INFO'] = environ['PATH_INFO'].replace(account,
                                                            new_tenant_name)
        return self.app(environ, start_response)


def filter_factory(global_conf, **local_conf):
    """Returns a WSGI filter app for use with paste.deploy."""
    conf = global_conf.copy()
    conf.update(local_conf)

    def auth_filter(app):
        return S3Token(app, conf)
    return auth_filter
