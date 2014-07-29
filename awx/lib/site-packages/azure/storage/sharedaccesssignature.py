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
from azure import url_quote
from azure.storage import _sign_string, X_MS_VERSION

#-------------------------------------------------------------------------
# Constants for the share access signature
SIGNED_START = 'st'
SIGNED_EXPIRY = 'se'
SIGNED_RESOURCE = 'sr'
SIGNED_PERMISSION = 'sp'
SIGNED_IDENTIFIER = 'si'
SIGNED_SIGNATURE = 'sig'
SIGNED_VERSION = 'sv'
RESOURCE_BLOB = 'b'
RESOURCE_CONTAINER = 'c'
SIGNED_RESOURCE_TYPE = 'resource'
SHARED_ACCESS_PERMISSION = 'permission'

#--------------------------------------------------------------------------


class WebResource(object):

    '''
    Class that stands for the resource to get the share access signature

    path: the resource path.
    properties: dict of name and values. Contains 2 item: resource type and
            permission
    request_url: the url of the webresource include all the queries.
    '''

    def __init__(self, path=None, request_url=None, properties=None):
        self.path = path
        self.properties = properties or {}
        self.request_url = request_url


class Permission(object):

    '''
    Permission class. Contains the path and query_string for the path.

    path: the resource path
    query_string: dict of name, values. Contains SIGNED_START, SIGNED_EXPIRY
            SIGNED_RESOURCE, SIGNED_PERMISSION, SIGNED_IDENTIFIER,
            SIGNED_SIGNATURE name values.
    '''

    def __init__(self, path=None, query_string=None):
        self.path = path
        self.query_string = query_string


class SharedAccessPolicy(object):

    ''' SharedAccessPolicy class. '''

    def __init__(self, access_policy, signed_identifier=None):
        self.id = signed_identifier
        self.access_policy = access_policy


class SharedAccessSignature(object):

    '''
    The main class used to do the signing and generating the signature.

    account_name:
        the storage account name used to generate shared access signature
    account_key: the access key to genenerate share access signature
    permission_set: the permission cache used to signed the request url.
    '''

    def __init__(self, account_name, account_key, permission_set=None):
        self.account_name = account_name
        self.account_key = account_key
        self.permission_set = permission_set

    def generate_signed_query_string(self, path, resource_type,
                                     shared_access_policy,
                                     version=X_MS_VERSION):
        '''
        Generates the query string for path, resource type and shared access
        policy.

        path: the resource
        resource_type: could be blob or container
        shared_access_policy: shared access policy
        version:
            x-ms-version for storage service, or None to get a signed query
            string compatible with pre 2012-02-12 clients, where the version
            is not included in the query string.
        '''

        query_string = {}
        if shared_access_policy.access_policy.start:
            query_string[
                SIGNED_START] = shared_access_policy.access_policy.start

        if version:
            query_string[SIGNED_VERSION] = version
        query_string[SIGNED_EXPIRY] = shared_access_policy.access_policy.expiry
        query_string[SIGNED_RESOURCE] = resource_type
        query_string[
            SIGNED_PERMISSION] = shared_access_policy.access_policy.permission

        if shared_access_policy.id:
            query_string[SIGNED_IDENTIFIER] = shared_access_policy.id

        query_string[SIGNED_SIGNATURE] = self._generate_signature(
            path, shared_access_policy, version)
        return query_string

    def sign_request(self, web_resource):
        ''' sign request to generate request_url with sharedaccesssignature
        info for web_resource.'''

        if self.permission_set:
            for shared_access_signature in self.permission_set:
                if self._permission_matches_request(
                        shared_access_signature, web_resource,
                        web_resource.properties[
                            SIGNED_RESOURCE_TYPE],
                        web_resource.properties[SHARED_ACCESS_PERMISSION]):
                    if web_resource.request_url.find('?') == -1:
                        web_resource.request_url += '?'
                    else:
                        web_resource.request_url += '&'

                    web_resource.request_url += self._convert_query_string(
                        shared_access_signature.query_string)
                    break
        return web_resource

    def _convert_query_string(self, query_string):
        ''' Converts query string to str. The order of name, values is very
        important and can't be wrong.'''

        convert_str = ''
        if SIGNED_START in query_string:
            convert_str += SIGNED_START + '=' + \
                url_quote(query_string[SIGNED_START]) + '&'
        convert_str += SIGNED_EXPIRY + '=' + \
            url_quote(query_string[SIGNED_EXPIRY]) + '&'
        convert_str += SIGNED_PERMISSION + '=' + \
            query_string[SIGNED_PERMISSION] + '&'
        convert_str += SIGNED_RESOURCE + '=' + \
            query_string[SIGNED_RESOURCE] + '&'

        if SIGNED_IDENTIFIER in query_string:
            convert_str += SIGNED_IDENTIFIER + '=' + \
                query_string[SIGNED_IDENTIFIER] + '&'
        if SIGNED_VERSION in query_string:
            convert_str += SIGNED_VERSION + '=' + \
                query_string[SIGNED_VERSION] + '&'
        convert_str += SIGNED_SIGNATURE + '=' + \
            url_quote(query_string[SIGNED_SIGNATURE]) + '&'
        return convert_str

    def _generate_signature(self, path, shared_access_policy, version):
        ''' Generates signature for a given path and shared access policy. '''

        def get_value_to_append(value, no_new_line=False):
            return_value = ''
            if value:
                return_value = value
            if not no_new_line:
                return_value += '\n'
            return return_value

        if path[0] != '/':
            path = '/' + path

        canonicalized_resource = '/' + self.account_name + path

        # Form the string to sign from shared_access_policy and canonicalized
        # resource. The order of values is important.
        string_to_sign = \
            (get_value_to_append(shared_access_policy.access_policy.permission) +
             get_value_to_append(shared_access_policy.access_policy.start) +
             get_value_to_append(shared_access_policy.access_policy.expiry) +
             get_value_to_append(canonicalized_resource))

        if version:
            string_to_sign += get_value_to_append(shared_access_policy.id)
            string_to_sign += get_value_to_append(version, True)
        else:
            string_to_sign += get_value_to_append(shared_access_policy.id, True)

        return self._sign(string_to_sign)

    def _permission_matches_request(self, shared_access_signature,
                                    web_resource, resource_type,
                                    required_permission):
        ''' Check whether requested permission matches given
        shared_access_signature, web_resource and resource type. '''

        required_resource_type = resource_type
        if required_resource_type == RESOURCE_BLOB:
            required_resource_type += RESOURCE_CONTAINER

        for name, value in shared_access_signature.query_string.items():
            if name == SIGNED_RESOURCE and \
                required_resource_type.find(value) == -1:
                return False
            elif name == SIGNED_PERMISSION and \
                required_permission.find(value) == -1:
                return False

        return web_resource.path.find(shared_access_signature.path) != -1

    def _sign(self, string_to_sign):
        ''' use HMAC-SHA256 to sign the string and convert it as base64
        encoded string. '''

        return _sign_string(self.account_key, string_to_sign)
