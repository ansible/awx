# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for Google Connection and Authentication classes.

Information about setting up your Google OAUTH2 credentials:

For libcloud, there are two basic methods for authenticating to Google using
OAUTH2: Service Accounts and Client IDs for Installed Applications.

Both are initially set up from the Cloud Console_
_Console: https://cloud.google.com/console

Setting up Service Account authentication (note that you need the PyCrypto
package installed to use this):
    - Go to the Console
    - Go to your project and then to "APIs & auth" on the left
    - Click on "Credentials"
    - Click on "Create New Client ID..."
    - Select "Service account" and click on "Create Client ID"
    - Download the Private Key (should happen automatically).
    - The key that you download is a PKCS12 key.  It needs to be converted to
      the PEM format.
    - Convert the key using OpenSSL (the default password is 'notasecret'):
      ``openssl pkcs12 -in YOURPRIVKEY.p12 -nodes -nocerts
      -passin pass:notasecret | openssl rsa -out PRIV.pem``
    - Move the .pem file to a safe location.
    - To Authenticate, you will need to pass the Service Account's "Email
      address" in as the user_id and the path to the .pem file as the key.

Setting up Installed Application authentication:
    - Go to the Console
    - Go to your project and then to "APIs & auth" on the left
    - Click on "Credentials"
    - Select "Installed application" and "Other" then click on
      "Create Client ID"
    - To Authenticate, pass in the "Client ID" as the user_id and the "Client
      secret" as the key
    - The first time that you do this, the libcloud will give you a URL to
      visit.  Copy and paste the URL into a browser.
    - When you go to the URL it will ask you to log in (if you aren't already)
      and ask you if you want to allow the project access to your account.
    - Click on Accept and you will be given a code.
    - Paste that code at the prompt given to you by the Google libcloud
      connection.
    - At that point, a token & refresh token will be stored in your home
      directory and will be used for authentication.

Please remember to secure your keys and access tokens.
"""
from __future__ import with_statement

try:
    import simplejson as json
except ImportError:
    import json

import base64
import errno
import time
import datetime
import os
import socket
import sys

from libcloud.utils.py3 import httplib, urlencode, urlparse, PY3
from libcloud.common.base import (ConnectionUserAndKey, JsonResponse,
                                  PollingConnection)
from libcloud.common.types import (ProviderError,
                                   LibcloudError)

try:
    from Crypto.Hash import SHA256
    from Crypto.PublicKey import RSA
    from Crypto.Signature import PKCS1_v1_5
    import Crypto.Random
    Crypto.Random.atfork()
except ImportError:
    # The pycrypto library is unavailable
    SHA256 = None
    RSA = None
    PKCS1_v1_5 = None

TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class GoogleAuthError(LibcloudError):
    """Generic Error class for various authentication errors."""
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return repr(self.value)


class GoogleBaseError(ProviderError):
    def __init__(self, value, http_code, code, driver=None):
        self.code = code
        super(GoogleBaseError, self).__init__(value, http_code, driver)


class InvalidRequestError(GoogleBaseError):
    pass


class JsonParseError(GoogleBaseError):
    pass


class ResourceNotFoundError(GoogleBaseError):
    pass


class QuotaExceededError(GoogleBaseError):
    pass


class ResourceExistsError(GoogleBaseError):
    pass


class ResourceInUseError(GoogleBaseError):
    pass


class GoogleResponse(JsonResponse):
    """
    Google Base Response class.
    """
    def success(self):
        """
        Determine if the request was successful.

        For the Google response class, tag all responses as successful and
        raise appropriate Exceptions from parse_body.

        :return: C{True}
        """
        return True

    def _get_error(self, body):
        """
        Get the error code and message from a JSON response.

        Return just the first error if there are multiple errors.

        :param  body: The body of the JSON response dictionary
        :type   body: ``dict``

        :return:  Tuple containing error code and message
        :rtype:   ``tuple`` of ``str`` or ``int``
        """
        if 'errors' in body['error']:
            err = body['error']['errors'][0]
        else:
            err = body['error']

        if 'code' in err:
            code = err.get('code')
            message = err.get('message')
        else:
            code = None
            message = body.get('error_description', err)

        return (code, message)

    def parse_body(self):
        """
        Parse the JSON response body, or raise exceptions as appropriate.

        :return:  JSON dictionary
        :rtype:   ``dict``
        """
        if len(self.body) == 0 and not self.parse_zero_length_body:
            return self.body

        json_error = False
        try:
            body = json.loads(self.body)
        except:
            # If there is both a JSON parsing error and an unsuccessful http
            # response (like a 404), we want to raise the http error and not
            # the JSON one, so don't raise JsonParseError here.
            body = self.body
            json_error = True

        if self.status in [httplib.OK, httplib.CREATED, httplib.ACCEPTED]:
            if json_error:
                raise JsonParseError(body, self.status, None)
            elif 'error' in body:
                (code, message) = self._get_error(body)
                if code == 'QUOTA_EXCEEDED':
                    raise QuotaExceededError(message, self.status, code)
                elif code == 'RESOURCE_ALREADY_EXISTS':
                    raise ResourceExistsError(message, self.status, code)
                elif code.startswith('RESOURCE_IN_USE'):
                    raise ResourceInUseError(message, self.status, code)
                else:
                    raise GoogleBaseError(message, self.status, code)
            else:
                return body

        elif self.status == httplib.NOT_FOUND:
            if (not json_error) and ('error' in body):
                (code, message) = self._get_error(body)
            else:
                message = body
                code = None
            raise ResourceNotFoundError(message, self.status, code)

        elif self.status == httplib.BAD_REQUEST:
            if (not json_error) and ('error' in body):
                (code, message) = self._get_error(body)
            else:
                message = body
                code = None
            raise InvalidRequestError(message, self.status, code)

        else:
            if (not json_error) and ('error' in body):
                (code, message) = self._get_error(body)
            else:
                message = body
                code = None
            raise GoogleBaseError(message, self.status, code)


class GoogleBaseDriver(object):
    name = "Google API"


class GoogleBaseAuthConnection(ConnectionUserAndKey):
    """
    Base class for Google Authentication.  Should be subclassed for specific
    types of authentication.
    """
    driver = GoogleBaseDriver
    responseCls = GoogleResponse
    name = 'Google Auth'
    host = 'accounts.google.com'
    auth_path = '/o/oauth2/auth'

    def __init__(self, user_id, key, scopes=None,
                 redirect_uri='urn:ietf:wg:oauth:2.0:oob',
                 login_hint=None, **kwargs):
        """
        :param  user_id: The email address (for service accounts) or Client ID
                         (for installed apps) to be used for authentication.
        :type   user_id: ``str``

        :param  key: The RSA Key (for service accounts) or file path containing
                     key or Client Secret (for installed apps) to be used for
                     authentication.
        :type   key: ``str``

        :param  scopes: A list of urls defining the scope of authentication
                       to grant.
        :type   scopes: ``list``

        :keyword  redirect_uri: The Redirect URI for the authentication
                                request.  See Google OAUTH2 documentation for
                                more info.
        :type     redirect_uri: ``str``

        :keyword  login_hint: Login hint for authentication request.  Useful
                              for Installed Application authentication.
        :type     login_hint: ``str``
        """
        scopes = scopes or []

        self.scopes = " ".join(scopes)
        self.redirect_uri = redirect_uri
        self.login_hint = login_hint

        super(GoogleBaseAuthConnection, self).__init__(user_id, key, **kwargs)

    def _now(self):
        return datetime.datetime.utcnow()

    def add_default_headers(self, headers):
        headers['Content-Type'] = "application/x-www-form-urlencoded"
        headers['Host'] = self.host
        return headers

    def _token_request(self, request_body):
        """
        Return an updated token from a token request body.

        :param  request_body: A dictionary of values to send in the body of the
                              token request.
        :type   request_body: ``dict``

        :return:  A dictionary with updated token information
        :rtype:   ``dict``
        """
        data = urlencode(request_body)
        now = self._now()
        response = self.request('/o/oauth2/token', method='POST', data=data)
        token_info = response.object
        if 'expires_in' in token_info:
            expire_time = now + datetime.timedelta(
                seconds=token_info['expires_in'])
            token_info['expire_time'] = expire_time.strftime(TIMESTAMP_FORMAT)
        return token_info


class GoogleInstalledAppAuthConnection(GoogleBaseAuthConnection):
    """Authentication connection for "Installed Application" authentication."""
    def get_code(self):
        """
        Give the user a URL that they can visit to authenticate and obtain a
        code.  This method will ask for that code that the user can paste in.

        :return:  Code supplied by the user after authenticating
        :rtype:   ``str``
        """
        auth_params = {'response_type': 'code',
                       'client_id': self.user_id,
                       'redirect_uri': self.redirect_uri,
                       'scope': self.scopes,
                       'state': 'Libcloud Request'}
        if self.login_hint:
            auth_params['login_hint'] = self.login_hint

        data = urlencode(auth_params)

        url = 'https://%s%s?%s' % (self.host, self.auth_path, data)
        print('Please Go to the following URL and sign in:')
        print(url)
        if PY3:
            code = input('Enter Code:')
        else:
            code = raw_input('Enter Code:')
        return code

    def get_new_token(self):
        """
        Get a new token. Generally used when no previous token exists or there
        is no refresh token

        :return:  Dictionary containing token information
        :rtype:   ``dict``
        """
        # Ask the user for a code
        code = self.get_code()

        token_request = {'code': code,
                         'client_id': self.user_id,
                         'client_secret': self.key,
                         'redirect_uri': self.redirect_uri,
                         'grant_type': 'authorization_code'}

        return self._token_request(token_request)

    def refresh_token(self, token_info):
        """
        Use the refresh token supplied in the token info to get a new token.

        :param  token_info: Dictionary containing current token information
        :type   token_info: ``dict``

        :return:  A dictionary containing updated token information.
        :rtype:   ``dict``
        """
        if 'refresh_token' not in token_info:
            return self.get_new_token()
        refresh_request = {'refresh_token': token_info['refresh_token'],
                           'client_id': self.user_id,
                           'client_secret': self.key,
                           'grant_type': 'refresh_token'}

        new_token = self._token_request(refresh_request)
        if 'refresh_token' not in new_token:
            new_token['refresh_token'] = token_info['refresh_token']
        return new_token


class GoogleServiceAcctAuthConnection(GoogleBaseAuthConnection):
    """Authentication class for "Service Account" authentication."""
    def __init__(self, user_id, key, *args, **kwargs):
        """
        Check to see if PyCrypto is available, and convert key file path into a
        key string if the key is in a file.

        :param  user_id: Email address to be used for Service Account
                authentication.
        :type   user_id: ``str``

        :param  key: The RSA Key or path to file containing the key.
        :type   key: ``str``
        """
        if SHA256 is None:
            raise GoogleAuthError('PyCrypto library required for '
                                  'Service Account Authentication.')
        # Check to see if 'key' is a file and read the file if it is.
        keypath = os.path.expanduser(key)
        is_file_path = os.path.exists(keypath) and os.path.isfile(keypath)
        if is_file_path:
            with open(keypath, 'r') as f:
                key = f.read()
        super(GoogleServiceAcctAuthConnection, self).__init__(
            user_id, key, *args, **kwargs)

    def get_new_token(self):
        """
        Get a new token using the email address and RSA Key.

        :return:  Dictionary containing token information
        :rtype:   ``dict``
        """
        # The header is always the same
        header = {'alg': 'RS256', 'typ': 'JWT'}
        header_enc = base64.urlsafe_b64encode(json.dumps(header))

        # Construct a claim set
        claim_set = {'iss': self.user_id,
                     'scope': self.scopes,
                     'aud': 'https://accounts.google.com/o/oauth2/token',
                     'exp': int(time.time()) + 3600,
                     'iat': int(time.time())}
        claim_set_enc = base64.urlsafe_b64encode(json.dumps(claim_set))

        # The message contains both the header and claim set
        message = '%s.%s' % (header_enc, claim_set_enc)
        # Then the message is signed using the key supplied
        key = RSA.importKey(self.key)
        hash_func = SHA256.new(message)
        signer = PKCS1_v1_5.new(key)
        signature = base64.urlsafe_b64encode(signer.sign(hash_func))

        # Finally the message and signature are sent to get a token
        jwt = '%s.%s' % (message, signature)
        request = {'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                   'assertion': jwt}

        return self._token_request(request)

    def refresh_token(self, token_info):
        """
        Refresh the current token.

        Service Account authentication doesn't supply a "refresh token" so
        this simply gets a new token using the email address/key.

        :param  token_info: Dictionary containing token information.
                            (Not used, but here for compatibility)
        :type   token_info: ``dict``

        :return:  A dictionary containing updated token information.
        :rtype:   ``dict``
        """
        return self.get_new_token()


class GoogleBaseConnection(ConnectionUserAndKey, PollingConnection):
    """Base connection class for interacting with Google APIs."""
    driver = GoogleBaseDriver
    responseCls = GoogleResponse
    host = 'www.googleapis.com'
    poll_interval = 2.0
    timeout = 180

    def __init__(self, user_id, key, auth_type=None,
                 credential_file=None, scopes=None, **kwargs):
        """
        Determine authentication type, set up appropriate authentication
        connection and get initial authentication information.

        :param  user_id: The email address (for service accounts) or Client ID
                         (for installed apps) to be used for authentication.
        :type   user_id: ``str``

        :param  key: The RSA Key (for service accounts) or file path containing
                     key or Client Secret (for installed apps) to be used for
                     authentication.
        :type   key: ``str``

        :keyword  auth_type: Accepted values are "SA" or "IA"
                             ("Service Account" or "Installed Application").
                             If not supplied, auth_type will be guessed based
                             on value of user_id.
        :type     auth_type: ``str``

        :keyword  credential_file: Path to file for caching authentication
                                   information.
        :type     credential_file: ``str``

        :keyword  scopes: List of OAuth2 scope URLs. The empty default sets
                          read/write access to Compute, Storage, and DNS.
        :type     scopes: ``list``
        """
        self.credential_file = credential_file or '~/.gce_libcloud_auth'

        if auth_type is None:
            # Try to guess.  Service accounts use an email address
            # as the user id.
            if '@' in user_id:
                auth_type = 'SA'
            else:
                auth_type = 'IA'

        # Default scopes to read/write for compute, storage, and dns.  Can
        # override this when calling get_driver() or setting in secrets.py
        self.scopes = scopes
        if not self.scopes:
            self.scopes = [
                'https://www.googleapis.com/auth/compute',
                'https://www.googleapis.com/auth/devstorage.full_control',
                'https://www.googleapis.com/auth/ndev.clouddns.readwrite',
            ]
        self.token_info = self._get_token_info_from_file()

        if auth_type == 'SA':
            self.auth_conn = GoogleServiceAcctAuthConnection(
                user_id, key, self.scopes, **kwargs)
        elif auth_type == 'IA':
            self.auth_conn = GoogleInstalledAppAuthConnection(
                user_id, key, self.scopes, **kwargs)
        else:
            raise GoogleAuthError('auth_type should be \'SA\' or \'IA\'')

        if self.token_info is None:
            self.token_info = self.auth_conn.get_new_token()
            self._write_token_info_to_file()

        self.token_expire_time = datetime.datetime.strptime(
            self.token_info['expire_time'], TIMESTAMP_FORMAT)

        super(GoogleBaseConnection, self).__init__(user_id, key, **kwargs)

        python_ver = '%s.%s.%s' % (sys.version_info[0], sys.version_info[1],
                                   sys.version_info[2])
        ver_platform = 'Python %s/%s' % (python_ver, sys.platform)
        self.user_agent_append(ver_platform)

    def _now(self):
        return datetime.datetime.utcnow()

    def add_default_headers(self, headers):
        """
        @inherits: :class:`Connection.add_default_headers`
        """
        headers['Content-Type'] = "application/json"
        headers['Host'] = self.host
        return headers

    def pre_connect_hook(self, params, headers):
        """
        Check to make sure that token hasn't expired.  If it has, get an
        updated token.  Also, add the token to the headers.

        @inherits: :class:`Connection.pre_connect_hook`
        """
        now = self._now()
        if self.token_expire_time < now:
            self.token_info = self.auth_conn.refresh_token(self.token_info)
            self.token_expire_time = datetime.datetime.strptime(
                self.token_info['expire_time'], TIMESTAMP_FORMAT)
            self._write_token_info_to_file()
        headers['Authorization'] = 'Bearer %s' % (
            self.token_info['access_token'])

        return params, headers

    def encode_data(self, data):
        """Encode data to JSON"""
        return json.dumps(data)

    def request(self, *args, **kwargs):
        """
        @inherits: :class:`Connection.request`
        """
        # Adds some retry logic for the occasional
        # "Connection Reset by peer" error.
        retries = 4
        tries = 0
        while tries < (retries - 1):
            try:
                return super(GoogleBaseConnection, self).request(
                    *args, **kwargs)
            except socket.error:
                e = sys.exc_info()[1]
                if e.errno == errno.ECONNRESET:
                    tries = tries + 1
                else:
                    raise e
        # One more time, then give up.
        return super(GoogleBaseConnection, self).request(*args, **kwargs)

    def _get_token_info_from_file(self):
        """
        Read credential file and return token information.

        :return:  Token information dictionary, or None
        :rtype:   ``dict`` or ``None``
        """
        token_info = None
        filename = os.path.realpath(os.path.expanduser(self.credential_file))

        try:
            with open(filename, 'r') as f:
                data = f.read()
            token_info = json.loads(data)
        except IOError:
            pass
        return token_info

    def _write_token_info_to_file(self):
        """
        Write token_info to credential file.
        """
        filename = os.path.realpath(os.path.expanduser(self.credential_file))
        data = json.dumps(self.token_info)
        with open(filename, 'w') as f:
            f.write(data)

    def has_completed(self, response):
        """
        Determine if operation has completed based on response.

        :param  response: JSON response
        :type   response: I{responseCls}

        :return:  True if complete, False otherwise
        :rtype:   ``bool``
        """
        if response.object['status'] == 'DONE':
            return True
        else:
            return False

    def get_poll_request_kwargs(self, response, context, request_kwargs):
        """
        @inherits: :class:`PollingConnection.get_poll_request_kwargs`
        """
        return {'action': response.object['selfLink']}

    def morph_action_hook(self, action):
        """
        Update action to correct request path.

        In many places, the Google API returns a full URL to a resource.
        This will strip the scheme and host off of the path and just return
        the request.  Otherwise, it will append the base request_path to
        the action.

        :param  action: The action to be called in the http request
        :type   action: ``str``

        :return:  The modified request based on the action
        :rtype:   ``str``
        """
        if action.startswith('https://'):
            u = urlparse.urlsplit(action)
            request = urlparse.urlunsplit(('', '', u[2], u[3], u[4]))
        else:
            request = self.request_path + action
        return request
