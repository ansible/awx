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

import argparse
import itertools
import logging
import uuid

import mock
from oslo_config import cfg
from oslo_config import fixture as config
from oslo_serialization import jsonutils
import requests
import six
from testtools import matchers

from keystoneclient import adapter
from keystoneclient.auth import base
from keystoneclient import exceptions
from keystoneclient.i18n import _
from keystoneclient import session as client_session
from keystoneclient.tests.unit import utils


class SessionTests(utils.TestCase):

    TEST_URL = 'http://127.0.0.1:5000/'

    def test_get(self):
        session = client_session.Session()
        self.stub_url('GET', text='response')
        resp = session.get(self.TEST_URL)

        self.assertEqual('GET', self.requests_mock.last_request.method)
        self.assertEqual(resp.text, 'response')
        self.assertTrue(resp.ok)

    def test_post(self):
        session = client_session.Session()
        self.stub_url('POST', text='response')
        resp = session.post(self.TEST_URL, json={'hello': 'world'})

        self.assertEqual('POST', self.requests_mock.last_request.method)
        self.assertEqual(resp.text, 'response')
        self.assertTrue(resp.ok)
        self.assertRequestBodyIs(json={'hello': 'world'})

    def test_head(self):
        session = client_session.Session()
        self.stub_url('HEAD')
        resp = session.head(self.TEST_URL)

        self.assertEqual('HEAD', self.requests_mock.last_request.method)
        self.assertTrue(resp.ok)
        self.assertRequestBodyIs('')

    def test_put(self):
        session = client_session.Session()
        self.stub_url('PUT', text='response')
        resp = session.put(self.TEST_URL, json={'hello': 'world'})

        self.assertEqual('PUT', self.requests_mock.last_request.method)
        self.assertEqual(resp.text, 'response')
        self.assertTrue(resp.ok)
        self.assertRequestBodyIs(json={'hello': 'world'})

    def test_delete(self):
        session = client_session.Session()
        self.stub_url('DELETE', text='response')
        resp = session.delete(self.TEST_URL)

        self.assertEqual('DELETE', self.requests_mock.last_request.method)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, 'response')

    def test_patch(self):
        session = client_session.Session()
        self.stub_url('PATCH', text='response')
        resp = session.patch(self.TEST_URL, json={'hello': 'world'})

        self.assertEqual('PATCH', self.requests_mock.last_request.method)
        self.assertTrue(resp.ok)
        self.assertEqual(resp.text, 'response')
        self.assertRequestBodyIs(json={'hello': 'world'})

    def test_user_agent(self):
        session = client_session.Session(user_agent='test-agent')
        self.stub_url('GET', text='response')
        resp = session.get(self.TEST_URL)

        self.assertTrue(resp.ok)
        self.assertRequestHeaderEqual('User-Agent', 'test-agent')

        resp = session.get(self.TEST_URL, headers={'User-Agent': 'new-agent'})
        self.assertTrue(resp.ok)
        self.assertRequestHeaderEqual('User-Agent', 'new-agent')

        resp = session.get(self.TEST_URL, headers={'User-Agent': 'new-agent'},
                           user_agent='overrides-agent')
        self.assertTrue(resp.ok)
        self.assertRequestHeaderEqual('User-Agent', 'overrides-agent')

    def test_http_session_opts(self):
        session = client_session.Session(cert='cert.pem', timeout=5,
                                         verify='certs')

        FAKE_RESP = utils.TestResponse({'status_code': 200, 'text': 'resp'})
        RESP = mock.Mock(return_value=FAKE_RESP)

        with mock.patch.object(session.session, 'request', RESP) as mocked:
            session.post(self.TEST_URL, data='value')

            mock_args, mock_kwargs = mocked.call_args

            self.assertEqual(mock_args[0], 'POST')
            self.assertEqual(mock_args[1], self.TEST_URL)
            self.assertEqual(mock_kwargs['data'], 'value')
            self.assertEqual(mock_kwargs['cert'], 'cert.pem')
            self.assertEqual(mock_kwargs['verify'], 'certs')
            self.assertEqual(mock_kwargs['timeout'], 5)

    def test_not_found(self):
        session = client_session.Session()
        self.stub_url('GET', status_code=404)
        self.assertRaises(exceptions.NotFound, session.get, self.TEST_URL)

    def test_server_error(self):
        session = client_session.Session()
        self.stub_url('GET', status_code=500)
        self.assertRaises(exceptions.InternalServerError,
                          session.get, self.TEST_URL)

    def test_session_debug_output(self):
        """Test request and response headers in debug logs

        in order to redact secure headers while debug is true.
        """
        session = client_session.Session(verify=False)
        headers = {'HEADERA': 'HEADERVALB'}
        security_headers = {'Authorization': uuid.uuid4().hex,
                            'X-Auth-Token': uuid.uuid4().hex,
                            'X-Subject-Token': uuid.uuid4().hex, }
        body = 'BODYRESPONSE'
        data = 'BODYDATA'
        all_headers = dict(
            itertools.chain(headers.items(), security_headers.items()))
        self.stub_url('POST', text=body, headers=all_headers)
        resp = session.post(self.TEST_URL, headers=all_headers, data=data)
        self.assertEqual(resp.status_code, 200)

        self.assertIn('curl', self.logger.output)
        self.assertIn('POST', self.logger.output)
        self.assertIn('--insecure', self.logger.output)
        self.assertIn(body, self.logger.output)
        self.assertIn("'%s'" % data, self.logger.output)

        for k, v in six.iteritems(headers):
            self.assertIn(k, self.logger.output)
            self.assertIn(v, self.logger.output)

        # Assert that response headers contains actual values and
        # only debug logs has been masked
        for k, v in six.iteritems(security_headers):
            self.assertIn('%s: {SHA1}' % k, self.logger.output)
            self.assertEqual(v, resp.headers[k])
            self.assertNotIn(v, self.logger.output)

    def test_logging_cacerts(self):
        path_to_certs = '/path/to/certs'
        session = client_session.Session(verify=path_to_certs)

        self.stub_url('GET', text='text')
        session.get(self.TEST_URL)

        self.assertIn('--cacert', self.logger.output)
        self.assertIn(path_to_certs, self.logger.output)

    def test_connect_retries(self):

        def _timeout_error(request, context):
            raise requests.exceptions.Timeout()

        self.stub_url('GET', text=_timeout_error)

        session = client_session.Session()
        retries = 3

        with mock.patch('time.sleep') as m:
            self.assertRaises(exceptions.RequestTimeout,
                              session.get,
                              self.TEST_URL, connect_retries=retries)

            self.assertEqual(retries, m.call_count)
            # 3 retries finishing with 2.0 means 0.5, 1.0 and 2.0
            m.assert_called_with(2.0)

        # we count retries so there will be one initial request + 3 retries
        self.assertThat(self.requests_mock.request_history,
                        matchers.HasLength(retries + 1))

    def test_uses_tcp_keepalive_by_default(self):
        session = client_session.Session()
        requests_session = session.session
        self.assertIsInstance(requests_session.adapters['http://'],
                              client_session.TCPKeepAliveAdapter)
        self.assertIsInstance(requests_session.adapters['https://'],
                              client_session.TCPKeepAliveAdapter)

    def test_does_not_set_tcp_keepalive_on_custom_sessions(self):
        mock_session = mock.Mock()
        client_session.Session(session=mock_session)
        self.assertFalse(mock_session.mount.called)

    def test_ssl_error_message(self):
        error = uuid.uuid4().hex

        def _ssl_error(request, context):
            raise requests.exceptions.SSLError(error)

        self.stub_url('GET', text=_ssl_error)
        session = client_session.Session()

        # The exception should contain the URL and details about the SSL error
        msg = _('SSL exception connecting to %(url)s: %(error)s') % {
            'url': self.TEST_URL, 'error': error}
        self.assertRaisesRegexp(exceptions.SSLError,
                                msg,
                                session.get,
                                self.TEST_URL)


class RedirectTests(utils.TestCase):

    REDIRECT_CHAIN = ['http://myhost:3445/',
                      'http://anotherhost:6555/',
                      'http://thirdhost/',
                      'http://finaldestination:55/']

    DEFAULT_REDIRECT_BODY = 'Redirect'
    DEFAULT_RESP_BODY = 'Found'

    def setup_redirects(self, method='GET', status_code=305,
                        redirect_kwargs={}, final_kwargs={}):
        redirect_kwargs.setdefault('text', self.DEFAULT_REDIRECT_BODY)

        for s, d in zip(self.REDIRECT_CHAIN, self.REDIRECT_CHAIN[1:]):
            self.requests_mock.register_uri(method, s, status_code=status_code,
                                            headers={'Location': d},
                                            **redirect_kwargs)

        final_kwargs.setdefault('status_code', 200)
        final_kwargs.setdefault('text', self.DEFAULT_RESP_BODY)
        self.requests_mock.register_uri(method, self.REDIRECT_CHAIN[-1],
                                        **final_kwargs)

    def assertResponse(self, resp):
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, self.DEFAULT_RESP_BODY)

    def test_basic_get(self):
        session = client_session.Session()
        self.setup_redirects()
        resp = session.get(self.REDIRECT_CHAIN[-2])
        self.assertResponse(resp)

    def test_basic_post_keeps_correct_method(self):
        session = client_session.Session()
        self.setup_redirects(method='POST', status_code=301)
        resp = session.post(self.REDIRECT_CHAIN[-2])
        self.assertResponse(resp)

    def test_redirect_forever(self):
        session = client_session.Session(redirect=True)
        self.setup_redirects()
        resp = session.get(self.REDIRECT_CHAIN[0])
        self.assertResponse(resp)
        self.assertTrue(len(resp.history), len(self.REDIRECT_CHAIN))

    def test_no_redirect(self):
        session = client_session.Session(redirect=False)
        self.setup_redirects()
        resp = session.get(self.REDIRECT_CHAIN[0])
        self.assertEqual(resp.status_code, 305)
        self.assertEqual(resp.url, self.REDIRECT_CHAIN[0])

    def test_redirect_limit(self):
        self.setup_redirects()
        for i in (1, 2):
            session = client_session.Session(redirect=i)
            resp = session.get(self.REDIRECT_CHAIN[0])
            self.assertEqual(resp.status_code, 305)
            self.assertEqual(resp.url, self.REDIRECT_CHAIN[i])
            self.assertEqual(resp.text, self.DEFAULT_REDIRECT_BODY)

    def test_history_matches_requests(self):
        self.setup_redirects(status_code=301)
        session = client_session.Session(redirect=True)
        req_resp = requests.get(self.REDIRECT_CHAIN[0],
                                allow_redirects=True)

        ses_resp = session.get(self.REDIRECT_CHAIN[0])

        self.assertEqual(len(req_resp.history), len(ses_resp.history))

        for r, s in zip(req_resp.history, ses_resp.history):
            self.assertEqual(r.url, s.url)
            self.assertEqual(r.status_code, s.status_code)


class ConstructSessionFromArgsTests(utils.TestCase):

    KEY = 'keyfile'
    CERT = 'certfile'
    CACERT = 'cacert-path'

    def _s(self, k=None, **kwargs):
        k = k or kwargs
        return client_session.Session.construct(k)

    def test_verify(self):
        self.assertFalse(self._s(insecure=True).verify)
        self.assertTrue(self._s(verify=True, insecure=True).verify)
        self.assertFalse(self._s(verify=False, insecure=True).verify)
        self.assertEqual(self._s(cacert=self.CACERT).verify, self.CACERT)

    def test_cert(self):
        tup = (self.CERT, self.KEY)
        self.assertEqual(self._s(cert=tup).cert, tup)
        self.assertEqual(self._s(cert=self.CERT, key=self.KEY).cert, tup)
        self.assertIsNone(self._s(key=self.KEY).cert)

    def test_pass_through(self):
        value = 42  # only a number because timeout needs to be
        for key in ['timeout', 'session', 'original_ip', 'user_agent']:
            args = {key: value}
            self.assertEqual(getattr(self._s(args), key), value)
            self.assertNotIn(key, args)


class AuthPlugin(base.BaseAuthPlugin):
    """Very simple debug authentication plugin.

    Takes Parameters such that it can throw exceptions at the right times.
    """

    TEST_TOKEN = 'aToken'
    TEST_USER_ID = 'aUser'
    TEST_PROJECT_ID = 'aProject'

    SERVICE_URLS = {
        'identity': {'public': 'http://identity-public:1111/v2.0',
                     'admin': 'http://identity-admin:1111/v2.0'},
        'compute': {'public': 'http://compute-public:2222/v1.0',
                    'admin': 'http://compute-admin:2222/v1.0'},
        'image': {'public': 'http://image-public:3333/v2.0',
                  'admin': 'http://image-admin:3333/v2.0'}
    }

    def __init__(self, token=TEST_TOKEN, invalidate=True):
        self.token = token
        self._invalidate = invalidate

    def get_token(self, session):
        return self.token

    def get_endpoint(self, session, service_type=None, interface=None,
                     **kwargs):
        try:
            return self.SERVICE_URLS[service_type][interface]
        except (KeyError, AttributeError):
            return None

    def invalidate(self):
        return self._invalidate

    def get_user_id(self, session):
        return self.TEST_USER_ID

    def get_project_id(self, session):
        return self.TEST_PROJECT_ID


class CalledAuthPlugin(base.BaseAuthPlugin):

    ENDPOINT = 'http://fakeendpoint/'

    def __init__(self, invalidate=True):
        self.get_token_called = False
        self.get_endpoint_called = False
        self.endpoint_arguments = {}
        self.invalidate_called = False
        self._invalidate = invalidate

    def get_token(self, session):
        self.get_token_called = True
        return 'aToken'

    def get_endpoint(self, session, **kwargs):
        self.get_endpoint_called = True
        self.endpoint_arguments = kwargs
        return self.ENDPOINT

    def invalidate(self):
        self.invalidate_called = True
        return self._invalidate


class SessionAuthTests(utils.TestCase):

    TEST_URL = 'http://127.0.0.1:5000/'
    TEST_JSON = {'hello': 'world'}

    def stub_service_url(self, service_type, interface, path,
                         method='GET', **kwargs):
        base_url = AuthPlugin.SERVICE_URLS[service_type][interface]
        uri = "%s/%s" % (base_url.rstrip('/'), path.lstrip('/'))

        self.requests_mock.register_uri(method, uri, **kwargs)

    def test_auth_plugin_default_with_plugin(self):
        self.stub_url('GET', base_url=self.TEST_URL, json=self.TEST_JSON)

        # if there is an auth_plugin then it should default to authenticated
        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        resp = sess.get(self.TEST_URL)
        self.assertDictEqual(resp.json(), self.TEST_JSON)

        self.assertRequestHeaderEqual('X-Auth-Token', AuthPlugin.TEST_TOKEN)

    def test_auth_plugin_disable(self):
        self.stub_url('GET', base_url=self.TEST_URL, json=self.TEST_JSON)

        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        resp = sess.get(self.TEST_URL, authenticated=False)
        self.assertDictEqual(resp.json(), self.TEST_JSON)

        self.assertRequestHeaderEqual('X-Auth-Token', None)

    def test_service_type_urls(self):
        service_type = 'compute'
        interface = 'public'
        path = '/instances'
        status = 200
        body = 'SUCCESS'

        self.stub_service_url(service_type=service_type,
                              interface=interface,
                              path=path,
                              status_code=status,
                              text=body)

        sess = client_session.Session(auth=AuthPlugin())
        resp = sess.get(path,
                        endpoint_filter={'service_type': service_type,
                                         'interface': interface})

        self.assertEqual(self.requests_mock.last_request.url,
                         AuthPlugin.SERVICE_URLS['compute']['public'] + path)
        self.assertEqual(resp.text, body)
        self.assertEqual(resp.status_code, status)

    def test_service_url_raises_if_no_auth_plugin(self):
        sess = client_session.Session()
        self.assertRaises(exceptions.MissingAuthPlugin,
                          sess.get, '/path',
                          endpoint_filter={'service_type': 'compute',
                                           'interface': 'public'})

    def test_service_url_raises_if_no_url_returned(self):
        sess = client_session.Session(auth=AuthPlugin())
        self.assertRaises(exceptions.EndpointNotFound,
                          sess.get, '/path',
                          endpoint_filter={'service_type': 'unknown',
                                           'interface': 'public'})

    def test_raises_exc_only_when_asked(self):
        # A request that returns a HTTP error should by default raise an
        # exception by default, if you specify raise_exc=False then it will not
        self.requests_mock.get(self.TEST_URL, status_code=401)

        sess = client_session.Session()
        self.assertRaises(exceptions.Unauthorized, sess.get, self.TEST_URL)

        resp = sess.get(self.TEST_URL, raise_exc=False)
        self.assertEqual(401, resp.status_code)

    def test_passed_auth_plugin(self):
        passed = CalledAuthPlugin()
        sess = client_session.Session()

        self.requests_mock.get(CalledAuthPlugin.ENDPOINT + 'path',
                               status_code=200)
        endpoint_filter = {'service_type': 'identity'}

        # no plugin with authenticated won't work
        self.assertRaises(exceptions.MissingAuthPlugin, sess.get, 'path',
                          authenticated=True)

        # no plugin with an endpoint filter won't work
        self.assertRaises(exceptions.MissingAuthPlugin, sess.get, 'path',
                          authenticated=False, endpoint_filter=endpoint_filter)

        resp = sess.get('path', auth=passed, endpoint_filter=endpoint_filter)

        self.assertEqual(200, resp.status_code)
        self.assertTrue(passed.get_endpoint_called)
        self.assertTrue(passed.get_token_called)

    def test_passed_auth_plugin_overrides(self):
        fixed = CalledAuthPlugin()
        passed = CalledAuthPlugin()

        sess = client_session.Session(fixed)

        self.requests_mock.get(CalledAuthPlugin.ENDPOINT + 'path',
                               status_code=200)

        resp = sess.get('path', auth=passed,
                        endpoint_filter={'service_type': 'identity'})

        self.assertEqual(200, resp.status_code)
        self.assertTrue(passed.get_endpoint_called)
        self.assertTrue(passed.get_token_called)
        self.assertFalse(fixed.get_endpoint_called)
        self.assertFalse(fixed.get_token_called)

    def test_requests_auth_plugin(self):
        sess = client_session.Session()

        requests_auth = object()

        FAKE_RESP = utils.TestResponse({'status_code': 200, 'text': 'resp'})
        RESP = mock.Mock(return_value=FAKE_RESP)

        with mock.patch.object(sess.session, 'request', RESP) as mocked:
            sess.get(self.TEST_URL, requests_auth=requests_auth)

            mocked.assert_called_once_with('GET', self.TEST_URL,
                                           headers=mock.ANY,
                                           allow_redirects=mock.ANY,
                                           auth=requests_auth,
                                           verify=mock.ANY)

    def test_reauth_called(self):
        auth = CalledAuthPlugin(invalidate=True)
        sess = client_session.Session(auth=auth)

        self.requests_mock.get(self.TEST_URL,
                               [{'text': 'Failed', 'status_code': 401},
                                {'text': 'Hello', 'status_code': 200}])

        # allow_reauth=True is the default
        resp = sess.get(self.TEST_URL, authenticated=True)

        self.assertEqual(200, resp.status_code)
        self.assertEqual('Hello', resp.text)
        self.assertTrue(auth.invalidate_called)

    def test_reauth_not_called(self):
        auth = CalledAuthPlugin(invalidate=True)
        sess = client_session.Session(auth=auth)

        self.requests_mock.get(self.TEST_URL,
                               [{'text': 'Failed', 'status_code': 401},
                                {'text': 'Hello', 'status_code': 200}])

        self.assertRaises(exceptions.Unauthorized, sess.get, self.TEST_URL,
                          authenticated=True, allow_reauth=False)
        self.assertFalse(auth.invalidate_called)

    def test_endpoint_override_overrides_filter(self):
        auth = CalledAuthPlugin()
        sess = client_session.Session(auth=auth)

        override_base = 'http://mytest/'
        path = 'path'
        override_url = override_base + path
        resp_text = uuid.uuid4().hex

        self.requests_mock.get(override_url, text=resp_text)

        resp = sess.get(path,
                        endpoint_override=override_base,
                        endpoint_filter={'service_type': 'identity'})

        self.assertEqual(resp_text, resp.text)
        self.assertEqual(override_url, self.requests_mock.last_request.url)

        self.assertTrue(auth.get_token_called)
        self.assertFalse(auth.get_endpoint_called)

    def test_endpoint_override_ignore_full_url(self):
        auth = CalledAuthPlugin()
        sess = client_session.Session(auth=auth)

        path = 'path'
        url = self.TEST_URL + path

        resp_text = uuid.uuid4().hex
        self.requests_mock.get(url, text=resp_text)

        resp = sess.get(url,
                        endpoint_override='http://someother.url',
                        endpoint_filter={'service_type': 'identity'})

        self.assertEqual(resp_text, resp.text)
        self.assertEqual(url, self.requests_mock.last_request.url)

        self.assertTrue(auth.get_token_called)
        self.assertFalse(auth.get_endpoint_called)

    def test_user_and_project_id(self):
        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)

        self.assertEqual(auth.TEST_USER_ID, sess.get_user_id())
        self.assertEqual(auth.TEST_PROJECT_ID, sess.get_project_id())

    def test_logger_object_passed(self):
        logger = logging.getLogger(uuid.uuid4().hex)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        io = six.StringIO()
        handler = logging.StreamHandler(io)
        logger.addHandler(handler)

        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        response = uuid.uuid4().hex

        self.stub_url('GET',
                      text=response,
                      headers={'Content-Type': 'text/html'})

        resp = sess.get(self.TEST_URL, logger=logger)

        self.assertEqual(response, resp.text)
        output = io.getvalue()

        self.assertIn(self.TEST_URL, output)
        self.assertIn(response, output)

        self.assertNotIn(self.TEST_URL, self.logger.output)
        self.assertNotIn(response, self.logger.output)


class AdapterTest(utils.TestCase):

    SERVICE_TYPE = uuid.uuid4().hex
    SERVICE_NAME = uuid.uuid4().hex
    INTERFACE = uuid.uuid4().hex
    REGION_NAME = uuid.uuid4().hex
    USER_AGENT = uuid.uuid4().hex
    VERSION = uuid.uuid4().hex

    TEST_URL = CalledAuthPlugin.ENDPOINT

    def _create_loaded_adapter(self):
        auth = CalledAuthPlugin()
        sess = client_session.Session()
        return adapter.Adapter(sess,
                               auth=auth,
                               service_type=self.SERVICE_TYPE,
                               service_name=self.SERVICE_NAME,
                               interface=self.INTERFACE,
                               region_name=self.REGION_NAME,
                               user_agent=self.USER_AGENT,
                               version=self.VERSION)

    def _verify_endpoint_called(self, adpt):
        self.assertEqual(self.SERVICE_TYPE,
                         adpt.auth.endpoint_arguments['service_type'])
        self.assertEqual(self.SERVICE_NAME,
                         adpt.auth.endpoint_arguments['service_name'])
        self.assertEqual(self.INTERFACE,
                         adpt.auth.endpoint_arguments['interface'])
        self.assertEqual(self.REGION_NAME,
                         adpt.auth.endpoint_arguments['region_name'])
        self.assertEqual(self.VERSION,
                         adpt.auth.endpoint_arguments['version'])

    def test_setting_variables_on_request(self):
        response = uuid.uuid4().hex
        self.stub_url('GET', text=response)
        adpt = self._create_loaded_adapter()
        resp = adpt.get('/')
        self.assertEqual(resp.text, response)

        self._verify_endpoint_called(adpt)
        self.assertTrue(adpt.auth.get_token_called)
        self.assertRequestHeaderEqual('User-Agent', self.USER_AGENT)

    def test_setting_variables_on_get_endpoint(self):
        adpt = self._create_loaded_adapter()
        url = adpt.get_endpoint()

        self.assertEqual(self.TEST_URL, url)
        self._verify_endpoint_called(adpt)

    def test_legacy_binding(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        response = jsonutils.dumps({key: val})

        self.stub_url('GET', text=response)

        auth = CalledAuthPlugin()
        sess = client_session.Session(auth=auth)
        adpt = adapter.LegacyJsonAdapter(sess,
                                         service_type=self.SERVICE_TYPE,
                                         user_agent=self.USER_AGENT)

        resp, body = adpt.get('/')
        self.assertEqual(self.SERVICE_TYPE,
                         auth.endpoint_arguments['service_type'])
        self.assertEqual(resp.text, response)
        self.assertEqual(val, body[key])

    def test_legacy_binding_non_json_resp(self):
        response = uuid.uuid4().hex
        self.stub_url('GET', text=response,
                      headers={'Content-Type': 'text/html'})

        auth = CalledAuthPlugin()
        sess = client_session.Session(auth=auth)
        adpt = adapter.LegacyJsonAdapter(sess,
                                         service_type=self.SERVICE_TYPE,
                                         user_agent=self.USER_AGENT)

        resp, body = adpt.get('/')
        self.assertEqual(self.SERVICE_TYPE,
                         auth.endpoint_arguments['service_type'])
        self.assertEqual(resp.text, response)
        self.assertIsNone(body)

    def test_methods(self):
        sess = client_session.Session()
        adpt = adapter.Adapter(sess)
        url = 'http://url'

        for method in ['get', 'head', 'post', 'put', 'patch', 'delete']:
            with mock.patch.object(adpt, 'request') as m:
                getattr(adpt, method)(url)
                m.assert_called_once_with(url, method.upper())

    def test_setting_endpoint_override(self):
        endpoint_override = 'http://overrideurl'
        path = '/path'
        endpoint_url = endpoint_override + path

        auth = CalledAuthPlugin()
        sess = client_session.Session(auth=auth)
        adpt = adapter.Adapter(sess, endpoint_override=endpoint_override)

        response = uuid.uuid4().hex
        self.requests_mock.get(endpoint_url, text=response)

        resp = adpt.get(path)

        self.assertEqual(response, resp.text)
        self.assertEqual(endpoint_url, self.requests_mock.last_request.url)

        self.assertEqual(endpoint_override, adpt.get_endpoint())

    def test_adapter_invalidate(self):
        auth = CalledAuthPlugin()
        sess = client_session.Session()
        adpt = adapter.Adapter(sess, auth=auth)

        adpt.invalidate()

        self.assertTrue(auth.invalidate_called)

    def test_adapter_get_token(self):
        auth = CalledAuthPlugin()
        sess = client_session.Session()
        adpt = adapter.Adapter(sess, auth=auth)

        self.assertEqual(self.TEST_TOKEN, adpt.get_token())
        self.assertTrue(auth.get_token_called)

    def test_adapter_connect_retries(self):
        retries = 2
        sess = client_session.Session()
        adpt = adapter.Adapter(sess, connect_retries=retries)

        def _refused_error(request, context):
            raise requests.exceptions.ConnectionError()

        self.stub_url('GET', text=_refused_error)

        with mock.patch('time.sleep') as m:
            self.assertRaises(exceptions.ConnectionRefused,
                              adpt.get, self.TEST_URL)
            self.assertEqual(retries, m.call_count)

        # we count retries so there will be one initial request + 2 retries
        self.assertThat(self.requests_mock.request_history,
                        matchers.HasLength(retries + 1))

    def test_user_and_project_id(self):
        auth = AuthPlugin()
        sess = client_session.Session()
        adpt = adapter.Adapter(sess, auth=auth)

        self.assertEqual(auth.TEST_USER_ID, adpt.get_user_id())
        self.assertEqual(auth.TEST_PROJECT_ID, adpt.get_project_id())

    def test_logger_object_passed(self):
        logger = logging.getLogger(uuid.uuid4().hex)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        io = six.StringIO()
        handler = logging.StreamHandler(io)
        logger.addHandler(handler)

        auth = AuthPlugin()
        sess = client_session.Session(auth=auth)
        adpt = adapter.Adapter(sess, auth=auth, logger=logger)

        response = uuid.uuid4().hex

        self.stub_url('GET', text=response,
                      headers={'Content-Type': 'text/html'})

        resp = adpt.get(self.TEST_URL, logger=logger)

        self.assertEqual(response, resp.text)
        output = io.getvalue()

        self.assertIn(self.TEST_URL, output)
        self.assertIn(response, output)

        self.assertNotIn(self.TEST_URL, self.logger.output)
        self.assertNotIn(response, self.logger.output)


class ConfLoadingTests(utils.TestCase):

    GROUP = 'sessiongroup'

    def setUp(self):
        super(ConfLoadingTests, self).setUp()

        self.conf_fixture = self.useFixture(config.Config())
        client_session.Session.register_conf_options(self.conf_fixture.conf,
                                                     self.GROUP)

    def config(self, **kwargs):
        kwargs['group'] = self.GROUP
        self.conf_fixture.config(**kwargs)

    def get_session(self, **kwargs):
        return client_session.Session.load_from_conf_options(
            self.conf_fixture.conf,
            self.GROUP,
            **kwargs)

    def test_insecure_timeout(self):
        self.config(insecure=True, timeout=5)
        s = self.get_session()

        self.assertFalse(s.verify)
        self.assertEqual(5, s.timeout)

    def test_client_certs(self):
        cert = '/path/to/certfile'
        key = '/path/to/keyfile'

        self.config(certfile=cert, keyfile=key)
        s = self.get_session()

        self.assertTrue(s.verify)
        self.assertEqual((cert, key), s.cert)

    def test_cacert(self):
        cafile = '/path/to/cacert'

        self.config(cafile=cafile)
        s = self.get_session()

        self.assertEqual(cafile, s.verify)

    def test_deprecated(self):
        def new_deprecated():
            return cfg.DeprecatedOpt(uuid.uuid4().hex, group=uuid.uuid4().hex)

        opt_names = ['cafile', 'certfile', 'keyfile', 'insecure', 'timeout']
        depr = dict([(n, [new_deprecated()]) for n in opt_names])
        opts = client_session.Session.get_conf_options(deprecated_opts=depr)

        self.assertThat(opt_names, matchers.HasLength(len(opts)))
        for opt in opts:
            self.assertIn(depr[opt.name][0], opt.deprecated_opts)


class CliLoadingTests(utils.TestCase):

    def setUp(self):
        super(CliLoadingTests, self).setUp()

        self.parser = argparse.ArgumentParser()
        client_session.Session.register_cli_options(self.parser)

    def get_session(self, val, **kwargs):
        args = self.parser.parse_args(val.split())
        return client_session.Session.load_from_cli_options(args, **kwargs)

    def test_insecure_timeout(self):
        s = self.get_session('--insecure --timeout 5.5')

        self.assertFalse(s.verify)
        self.assertEqual(5.5, s.timeout)

    def test_client_certs(self):
        cert = '/path/to/certfile'
        key = '/path/to/keyfile'

        s = self.get_session('--os-cert %s --os-key %s' % (cert, key))

        self.assertTrue(s.verify)
        self.assertEqual((cert, key), s.cert)

    def test_cacert(self):
        cacert = '/path/to/cacert'

        s = self.get_session('--os-cacert %s' % cacert)

        self.assertEqual(cacert, s.verify)
