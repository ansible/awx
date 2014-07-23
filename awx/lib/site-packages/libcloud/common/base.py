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

import os
import sys
import ssl
import copy
import binascii
import time

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from pipes import quote as pquote

try:
    import simplejson as json
except:
    import json

import libcloud

from libcloud.utils.py3 import PY3, PY25
from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlparse
from libcloud.utils.py3 import urlencode
from libcloud.utils.py3 import StringIO
from libcloud.utils.py3 import u
from libcloud.utils.py3 import b

from libcloud.utils.misc import lowercase_keys
from libcloud.utils.compression import decompress_data
from libcloud.common.types import LibcloudError, MalformedResponseError

from libcloud.httplib_ssl import LibcloudHTTPSConnection

LibcloudHTTPConnection = httplib.HTTPConnection


class HTTPResponse(httplib.HTTPResponse):
    # On python 2.6 some calls can hang because HEAD isn't quite properly
    # supported.
    # In particular this happens on S3 when calls are made to get_object to
    # objects that don't exist.
    # This applies the behaviour from 2.7, fixing the hangs.
    def read(self, amt=None):
        if self.fp is None:
            return ''

        if self._method == 'HEAD':
            self.close()
            return ''

        return httplib.HTTPResponse.read(self, amt)


class Response(object):
    """
    A base Response class to derive from.
    """

    status = httplib.OK  # Response status code
    headers = {}  # Response headers
    body = None  # Raw response body
    object = None  # Parsed response body

    error = None  # Reason returned by the server.
    connection = None  # Parent connection class
    parse_zero_length_body = False

    def __init__(self, response, connection):
        """
        :param response: HTTP response object. (optional)
        :type response: :class:`httplib.HTTPResponse`

        :param connection: Parent connection object.
        :type connection: :class:`.Connection`
        """
        self.connection = connection

        # http.client In Python 3 doesn't automatically lowercase the header
        # names
        self.headers = lowercase_keys(dict(response.getheaders()))
        self.error = response.reason
        self.status = response.status

        # This attribute is set when using LoggingConnection.
        original_data = getattr(response, '_original_data', None)

        if original_data:
            # LoggingConnection already decompresses data so it can log it
            # which means we don't need to decompress it here.
            self.body = response._original_data
        else:
            self.body = self._decompress_response(body=response.read(),
                                                  headers=self.headers)

        if PY3:
            self.body = b(self.body).decode('utf-8')

        if not self.success():
            raise Exception(self.parse_error())

        self.object = self.parse_body()

    def parse_body(self):
        """
        Parse response body.

        Override in a provider's subclass.

        :return: Parsed body.
        :rtype: ``str``
        """
        return self.body

    def parse_error(self):
        """
        Parse the error messages.

        Override in a provider's subclass.

        :return: Parsed error.
        :rtype: ``str``
        """
        return self.body

    def success(self):
        """
        Determine if our request was successful.

        The meaning of this can be arbitrary; did we receive OK status? Did
        the node get created? Were we authenticated?

        :rtype: ``bool``
        :return: ``True`` or ``False``
        """
        return self.status in [httplib.OK, httplib.CREATED]

    def _decompress_response(self, body, headers):
        """
        Decompress a response body if it is using deflate or gzip encoding.

        :param body: Response body.
        :type body: ``str``

        :param headers: Response headers.
        :type headers: ``dict``

        :return: Decompressed response
        :rtype: ``str``
        """
        encoding = headers.get('content-encoding', None)

        if encoding in ['zlib', 'deflate']:
            body = decompress_data('zlib', body)
        elif encoding in ['gzip', 'x-gzip']:
            body = decompress_data('gzip', body)
        else:
            body = body.strip()

        return body


class JsonResponse(Response):
    """
    A Base JSON Response class to derive from.
    """

    def parse_body(self):
        if len(self.body) == 0 and not self.parse_zero_length_body:
            return self.body

        try:
            body = json.loads(self.body)
        except:
            raise MalformedResponseError(
                'Failed to parse JSON',
                body=self.body,
                driver=self.connection.driver)
        return body

    parse_error = parse_body


class XmlResponse(Response):
    """
    A Base XML Response class to derive from.
    """

    def parse_body(self):
        if len(self.body) == 0 and not self.parse_zero_length_body:
            return self.body

        try:
            body = ET.XML(self.body)
        except:
            raise MalformedResponseError('Failed to parse XML',
                                         body=self.body,
                                         driver=self.connection.driver)
        return body

    parse_error = parse_body


class RawResponse(Response):

    def __init__(self, connection):
        """
        :param connection: Parent connection object.
        :type connection: :class:`.Connection`
        """
        self._status = None
        self._response = None
        self._headers = {}
        self._error = None
        self._reason = None
        self.connection = connection

    @property
    def response(self):
        if not self._response:
            response = self.connection.connection.getresponse()
            self._response, self.body = response, response
            if not self.success():
                self.parse_error()
        return self._response

    @property
    def status(self):
        if not self._status:
            self._status = self.response.status
        return self._status

    @property
    def headers(self):
        if not self._headers:
            self._headers = lowercase_keys(dict(self.response.getheaders()))
        return self._headers

    @property
    def reason(self):
        if not self._reason:
            self._reason = self.response.reason
        return self._reason


# TODO: Move this to a better location/package
class LoggingConnection():
    """
    Debug class to log all HTTP(s) requests as they could be made
    with the curl command.

    :cvar log: file-like object that logs entries are written to.
    """
    log = None

    def _log_response(self, r):
        rv = "# -------- begin %d:%d response ----------\n" % (id(self), id(r))
        ht = ""
        v = r.version
        if r.version == 10:
            v = "HTTP/1.0"
        if r.version == 11:
            v = "HTTP/1.1"
        ht += "%s %s %s\r\n" % (v, r.status, r.reason)
        body = r.read()
        for h in r.getheaders():
            ht += "%s: %s\r\n" % (h[0].title(), h[1])
        ht += "\r\n"

        # this is evil. laugh with me. ha arharhrhahahaha
        class fakesock:
            def __init__(self, s):
                self.s = s

            def makefile(self, *args, **kwargs):
                if PY3:
                    from io import BytesIO
                    cls = BytesIO
                else:
                    cls = StringIO

                return cls(b(self.s))
        rr = r
        headers = lowercase_keys(dict(r.getheaders()))

        encoding = headers.get('content-encoding', None)

        if encoding in ['zlib', 'deflate']:
            body = decompress_data('zlib', body)
        elif encoding in ['gzip', 'x-gzip']:
            body = decompress_data('gzip', body)

        if r.chunked:
            ht += "%x\r\n" % (len(body))
            ht += u(body)
            ht += "\r\n0\r\n"
        else:
            ht += u(body)

        if sys.version_info >= (2, 6) and sys.version_info < (2, 7):
            cls = HTTPResponse
        else:
            cls = httplib.HTTPResponse

        rr = cls(sock=fakesock(ht), method=r._method,
                 debuglevel=r.debuglevel)
        rr.begin()
        rv += ht
        rv += ("\n# -------- end %d:%d response ----------\n"
               % (id(self), id(r)))

        rr._original_data = body
        return (rr, rv)

    def _log_curl(self, method, url, body, headers):
        cmd = ["curl", "-i"]

        if method.lower() == 'head':
            # HEAD method need special handling
            cmd.extend(["--head"])
        else:
            cmd.extend(["-X", pquote(method)])

        for h in headers:
            cmd.extend(["-H", pquote("%s: %s" % (h, headers[h]))])

        # TODO: in python 2.6, body can be a file-like object.
        if body is not None and len(body) > 0:
            cmd.extend(["--data-binary", pquote(body)])

        cmd.extend(["--compress"])
        cmd.extend([pquote("%s://%s:%d%s" % (self.protocol, self.host,
                                             self.port, url))])
        return " ".join(cmd)


class LoggingHTTPSConnection(LoggingConnection, LibcloudHTTPSConnection):
    """
    Utility Class for logging HTTPS connections
    """

    protocol = 'https'

    def getresponse(self):
        r = LibcloudHTTPSConnection.getresponse(self)
        if self.log is not None:
            r, rv = self._log_response(r)
            self.log.write(rv + "\n")
            self.log.flush()
        return r

    def request(self, method, url, body=None, headers=None):
        headers.update({'X-LC-Request-ID': str(id(self))})
        if self.log is not None:
            pre = "# -------- begin %d request ----------\n" % id(self)
            self.log.write(pre +
                           self._log_curl(method, url, body, headers) + "\n")
            self.log.flush()
        return LibcloudHTTPSConnection.request(self, method, url, body,
                                               headers)


class LoggingHTTPConnection(LoggingConnection, LibcloudHTTPConnection):
    """
    Utility Class for logging HTTP connections
    """

    protocol = 'http'

    def getresponse(self):
        r = LibcloudHTTPConnection.getresponse(self)
        if self.log is not None:
            r, rv = self._log_response(r)
            self.log.write(rv + "\n")
            self.log.flush()
        return r

    def request(self, method, url, body=None, headers=None):
        headers.update({'X-LC-Request-ID': str(id(self))})
        if self.log is not None:
            pre = '# -------- begin %d request ----------\n' % id(self)
            self.log.write(pre +
                           self._log_curl(method, url, body, headers) + "\n")
            self.log.flush()
        return LibcloudHTTPConnection.request(self, method, url,
                                              body, headers)


class Connection(object):
    """
    A Base Connection class to derive from.
    """
    # conn_classes = (LoggingHTTPSConnection)
    conn_classes = (LibcloudHTTPConnection, LibcloudHTTPSConnection)

    responseCls = Response
    rawResponseCls = RawResponse
    connection = None
    host = '127.0.0.1'
    port = 443
    timeout = None
    secure = 1
    driver = None
    action = None
    cache_busting = False

    allow_insecure = True

    def __init__(self, secure=True, host=None, port=None, url=None,
                 timeout=None):
        self.secure = secure and 1 or 0
        self.ua = []
        self.context = {}

        if not self.allow_insecure and not secure:
            # TODO: We should eventually switch to whitelist instead of
            # blacklist approach
            raise ValueError('Non https connections are not allowed (use '
                             'secure=True)')

        self.request_path = ''

        if host:
            self.host = host

        if port is not None:
            self.port = port
        else:
            if self.secure == 1:
                self.port = 443
            else:
                self.port = 80

        if url:
            (self.host, self.port, self.secure,
             self.request_path) = self._tuple_from_url(url)

        if timeout:
            self.timeout = timeout

    def set_context(self, context):
        if not isinstance(context, dict):
            raise TypeError('context needs to be a dictionary')

        self.context = context

    def reset_context(self):
        self.context = {}

    def _tuple_from_url(self, url):
        secure = 1
        port = None
        (scheme, netloc, request_path, param,
         query, fragment) = urlparse.urlparse(url)

        if scheme not in ['http', 'https']:
            raise LibcloudError('Invalid scheme: %s in url %s' % (scheme, url))

        if scheme == "http":
            secure = 0

        if ":" in netloc:
            netloc, port = netloc.rsplit(":")
            port = port

        if not port:
            if scheme == "http":
                port = 80
            else:
                port = 443

        host = netloc

        return (host, port, secure, request_path)

    def connect(self, host=None, port=None, base_url=None):
        """
        Establish a connection with the API server.

        :type host: ``str``
        :param host: Optional host to override our default

        :type port: ``int``
        :param port: Optional port to override our default

        :returns: A connection
        """
        # prefer the attribute base_url if its set or sent
        connection = None
        secure = self.secure

        if getattr(self, 'base_url', None) and base_url is None:
            (host, port,
             secure, request_path) = self._tuple_from_url(self.base_url)
        elif base_url is not None:
            (host, port,
             secure, request_path) = self._tuple_from_url(base_url)
        else:
            host = host or self.host
            port = port or self.port

        kwargs = {'host': host, 'port': int(port)}

        # Timeout is only supported in Python 2.6 and later
        # http://docs.python.org/library/httplib.html#httplib.HTTPConnection
        if self.timeout and not PY25:
            kwargs.update({'timeout': self.timeout})

        connection = self.conn_classes[secure](**kwargs)
        # You can uncoment this line, if you setup a reverse proxy server
        # which proxies to your endpoint, and lets you easily capture
        # connections in cleartext when you setup the proxy to do SSL
        # for you
        # connection = self.conn_classes[False]("127.0.0.1", 8080)

        self.connection = connection

    def _user_agent(self):
        user_agent_suffix = ' '.join(['(%s)' % x for x in self.ua])

        if self.driver:
            user_agent = 'libcloud/%s (%s) %s' % (
                libcloud.__version__,
                self.driver.name, user_agent_suffix)
        else:
            user_agent = 'libcloud/%s %s' % (
                libcloud.__version__, user_agent_suffix)

        return user_agent

    def user_agent_append(self, token):
        """
        Append a token to a user agent string.

        Users of the library should call this to uniquely identify their
        requests to a provider.

        :type token: ``str``
        :param token: Token to add to the user agent.
        """
        self.ua.append(token)

    def request(self, action, params=None, data=None, headers=None,
                method='GET', raw=False):
        """
        Request a given `action`.

        Basically a wrapper around the connection
        object's `request` that does some helpful pre-processing.

        :type action: ``str``
        :param action: A path. This can include arguments. If included,
            any extra parameters are appended to the existing ones.

        :type params: ``dict``
        :param params: Optional mapping of additional parameters to send. If
            None, leave as an empty ``dict``.

        :type data: ``unicode``
        :param data: A body of data to send with the request.

        :type headers: ``dict``
        :param headers: Extra headers to add to the request
            None, leave as an empty ``dict``.

        :type method: ``str``
        :param method: An HTTP method such as "GET" or "POST".

        :type raw: ``bool``
        :param raw: True to perform a "raw" request aka only send the headers
                     and use the rawResponseCls class. This is used with
                     storage API when uploading a file.

        :return: An :class:`Response` instance.
        :rtype: :class:`Response` instance

        """
        if params is None:
            params = {}
        else:
            params = copy.copy(params)

        if headers is None:
            headers = {}
        else:
            headers = copy.copy(headers)

        action = self.morph_action_hook(action)
        self.action = action
        self.method = method

        # Extend default parameters
        params = self.add_default_params(params)

        # Add cache busting parameters (if enabled)
        if self.cache_busting and method == 'GET':
            params = self._add_cache_busting_to_params(params=params)

        # Extend default headers
        headers = self.add_default_headers(headers)

        # We always send a user-agent header
        headers.update({'User-Agent': self._user_agent()})

        # Indicate that we support gzip and deflate compression
        headers.update({'Accept-Encoding': 'gzip,deflate'})

        port = int(self.port)

        if port not in (80, 443):
            headers.update({'Host': "%s:%d" % (self.host, port)})
        else:
            headers.update({'Host': self.host})

        if data:
            data = self.encode_data(data)
            headers['Content-Length'] = str(len(data))
        elif method.upper() in ['POST', 'PUT'] and not raw:
            # Only send Content-Length 0 with POST and PUT request.
            #
            # Note: Content-Length is not added when using "raw" mode means
            # means that headers are upfront and the body is sent at some point
            # later on. With raw mode user can specify Content-Length with
            # "data" not being set.
            headers['Content-Length'] = '0'

        params, headers = self.pre_connect_hook(params, headers)

        if params:
            if '?' in action:
                url = '&'.join((action, urlencode(params, doseq=True)))
            else:
                url = '?'.join((action, urlencode(params, doseq=True)))
        else:
            url = action

        # Removed terrible hack...this a less-bad hack that doesn't execute a
        # request twice, but it's still a hack.
        self.connect()
        try:
            # @TODO: Should we just pass File object as body to request method
            # instead of dealing with splitting and sending the file ourselves?
            if raw:
                self.connection.putrequest(method, url)

                for key, value in list(headers.items()):
                    self.connection.putheader(key, str(value))

                self.connection.endheaders()
            else:
                self.connection.request(method=method, url=url, body=data,
                                        headers=headers)
        except ssl.SSLError:
            e = sys.exc_info()[1]
            self.reset_context()
            raise ssl.SSLError(str(e))

        if raw:
            responseCls = self.rawResponseCls
            kwargs = {'connection': self}
        else:
            responseCls = self.responseCls
            kwargs = {'connection': self,
                      'response': self.connection.getresponse()}

        try:
            response = responseCls(**kwargs)
        finally:
            # Always reset the context after the request has completed
            self.reset_context()

        return response

    def morph_action_hook(self, action):
        return self.request_path + action

    def add_default_params(self, params):
        """
        Adds default parameters (such as API key, version, etc.)
        to the passed `params`

        Should return a dictionary.
        """
        return params

    def add_default_headers(self, headers):
        """
        Adds default headers (such as Authorization, X-Foo-Bar)
        to the passed `headers`

        Should return a dictionary.
        """
        return headers

    def pre_connect_hook(self, params, headers):
        """
        A hook which is called before connecting to the remote server.
        This hook can perform a final manipulation on the params, headers and
        url parameters.

        :type params: ``dict``
        :param params: Request parameters.

        :type headers: ``dict``
        :param headers: Request headers.
        """
        return params, headers

    def encode_data(self, data):
        """
        Encode body data.

        Override in a provider's subclass.
        """
        return data

    def _add_cache_busting_to_params(self, params):
        """
        Add cache busting parameter to the query parameters of a GET request.

        Parameters are only added if "cache_busting" class attribute is set to
        True.

        Note: This should only be used with *naughty* providers which use
        excessive caching of responses.
        """
        cache_busting_value = binascii.hexlify(os.urandom(8)).decode('ascii')

        if isinstance(params, dict):
            params['cache-busting'] = cache_busting_value
        else:
            params.append(('cache-busting', cache_busting_value))

        return params


class PollingConnection(Connection):
    """
    Connection class which can also work with the async APIs.

    After initial requests, this class periodically polls for jobs status and
    waits until the job has finished.
    If job doesn't finish in timeout seconds, an Exception thrown.
    """
    poll_interval = 0.5
    timeout = 200
    request_method = 'request'

    def async_request(self, action, params=None, data=None, headers=None,
                      method='GET', context=None):
        """
        Perform an 'async' request to the specified path. Keep in mind that
        this function is *blocking* and 'async' in this case means that the
        hit URL only returns a job ID which is the periodically polled until
        the job has completed.

        This function works like this:

        - Perform a request to the specified path. Response should contain a
          'job_id'.

        - Returned 'job_id' is then used to construct a URL which is used for
          retrieving job status. Constructed URL is then periodically polled
          until the response indicates that the job has completed or the
          timeout of 'self.timeout' seconds has been reached.

        :type action: ``str``
        :param action: A path

        :type params: ``dict``
        :param params: Optional mapping of additional parameters to send. If
            None, leave as an empty ``dict``.

        :type data: ``unicode``
        :param data: A body of data to send with the request.

        :type headers: ``dict``
        :param headers: Extra headers to add to the request
            None, leave as an empty ``dict``.

        :type method: ``str``
        :param method: An HTTP method such as "GET" or "POST".

        :type context: ``dict``
        :param context: Context dictionary which is passed to the functions
        which construct initial and poll URL.

        :return: An :class:`Response` instance.
        :rtype: :class:`Response` instance
        """

        request = getattr(self, self.request_method)
        kwargs = self.get_request_kwargs(action=action, params=params,
                                         data=data, headers=headers,
                                         method=method,
                                         context=context)
        response = request(**kwargs)
        kwargs = self.get_poll_request_kwargs(response=response,
                                              context=context,
                                              request_kwargs=kwargs)

        end = time.time() + self.timeout
        completed = False
        while time.time() < end and not completed:
            response = request(**kwargs)
            completed = self.has_completed(response=response)
            if not completed:
                time.sleep(self.poll_interval)

        if not completed:
            raise LibcloudError('Job did not complete in %s seconds' %
                                (self.timeout))

        return response

    def get_request_kwargs(self, action, params=None, data=None, headers=None,
                           method='GET', context=None):
        """
        Arguments which are passed to the initial request() call inside
        async_request.
        """
        kwargs = {'action': action, 'params': params, 'data': data,
                  'headers': headers, 'method': method}
        return kwargs

    def get_poll_request_kwargs(self, response, context, request_kwargs):
        """
        Return keyword arguments which are passed to the request() method when
        polling for the job status.

        :param response: Response object returned by poll request.
        :type response: :class:`HTTPResponse`

        :param request_kwargs: Kwargs previously used to initiate the
                                  poll request.
        :type response: ``dict``

        :return ``dict`` Keyword arguments
        """
        raise NotImplementedError('get_poll_request_kwargs not implemented')

    def has_completed(self, response):
        """
        Return job completion status.

        :param response: Response object returned by poll request.
        :type response: :class:`HTTPResponse`

        :return ``bool`` True if the job has completed, False otherwise.
        """
        raise NotImplementedError('has_completed not implemented')


class ConnectionKey(Connection):
    """
    Base connection class which accepts a single ``key`` argument.
    """
    def __init__(self, key, secure=True, host=None, port=None, url=None,
                 timeout=None):
        """
        Initialize `user_id` and `key`; set `secure` to an ``int`` based on
        passed value.
        """
        super(ConnectionKey, self).__init__(secure=secure, host=host,
                                            port=port, url=url,
                                            timeout=timeout)
        self.key = key


class ConnectionUserAndKey(ConnectionKey):
    """
    Base connection class which accepts a ``user_id`` and ``key`` argument.
    """

    user_id = None

    def __init__(self, user_id, key, secure=True,
                 host=None, port=None, url=None, timeout=None):
        super(ConnectionUserAndKey, self).__init__(key, secure=secure,
                                                   host=host, port=port,
                                                   url=url, timeout=timeout)
        self.user_id = user_id


class BaseDriver(object):
    """
    Base driver class from which other classes can inherit from.
    """

    connectionCls = ConnectionKey

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 api_version=None, region=None, **kwargs):
        """
        :param    key:    API key or username to be used (required)
        :type     key:    ``str``

        :param    secret: Secret password to be used (required)
        :type     secret: ``str``

        :param    secure: Weither to use HTTPS or HTTP. Note: Some providers
                            only support HTTPS, and it is on by default.
        :type     secure: ``bool``

        :param    host: Override hostname used for connections.
        :type     host: ``str``

        :param    port: Override port used for connections.
        :type     port: ``int``

        :param    api_version: Optional API version. Only used by drivers
                                 which support multiple API versions.
        :type     api_version: ``str``

        :param region: Optional driver region. Only used by drivers which
                       support multiple regions.
        :type region: ``str``

        :rtype: ``None``
        """

        self.key = key
        self.secret = secret
        self.secure = secure
        args = [self.key]

        if self.secret is not None:
            args.append(self.secret)

        args.append(secure)

        if host is not None:
            args.append(host)

        if port is not None:
            args.append(port)

        self.api_version = api_version
        self.region = region

        conn_kwargs = self._ex_connection_class_kwargs()
        self.connection = self.connectionCls(*args, **conn_kwargs)

        self.connection.driver = self
        self.connection.connect()

    def _ex_connection_class_kwargs(self):
        """
        Return extra connection keyword arguments which are passed to the
        Connection class constructor.
        """
        return {}
