# -*- coding: utf-8 -*-
import base64
import logging
import socket
import datetime
from dateutil.tz import tzutc
from io import StringIO
from uuid import uuid4

from unittest import mock

from django.conf import LazySettings
from django.utils.encoding import smart_str
import pytest
import requests
from requests_futures.sessions import FuturesSession

from awx.main.utils.handlers import (BaseHandler, BaseHTTPSHandler as HTTPSHandler,
                                     TCPHandler, UDPHandler, _encode_payload_for_socket,
                                     PARAM_NAMES, LoggingConnectivityException,
                                     AWXProxyHandler)
from awx.main.utils.formatters import LogstashFormatter


@pytest.fixture()
def https_adapter():
    class FakeHTTPSAdapter(requests.adapters.HTTPAdapter):
        requests = []
        status = 200
        reason = None

        def send(self, request, **kwargs):
            self.requests.append(request)
            resp = requests.models.Response()
            resp.status_code = self.status
            resp.reason = self.reason
            resp.request = request
            return resp

    return FakeHTTPSAdapter()


@pytest.fixture()
def connection_error_adapter():
    class ConnectionErrorAdapter(requests.adapters.HTTPAdapter):

        def send(self, request, **kwargs):
            err = requests.packages.urllib3.exceptions.SSLError()
            raise requests.exceptions.ConnectionError(err, request=request)

    return ConnectionErrorAdapter()


@pytest.fixture
def fake_socket(tmpdir_factory, request):
    sok = socket.socket
    sok.send = mock.MagicMock()
    sok.connect = mock.MagicMock()
    sok.setblocking = mock.MagicMock()
    sok.close = mock.MagicMock()
    return sok


def test_https_logging_handler_requests_async_implementation():
    handler = HTTPSHandler()
    assert isinstance(handler.session, FuturesSession)


def test_https_logging_handler_has_default_http_timeout():
    handler = TCPHandler()
    assert handler.tcp_timeout == 5


@pytest.mark.parametrize('param', ['host', 'port', 'indv_facts'])
def test_base_logging_handler_defaults(param):
    handler = BaseHandler()
    assert hasattr(handler, param) and getattr(handler, param) is None


@pytest.mark.parametrize('param', ['host', 'port', 'indv_facts'])
def test_base_logging_handler_kwargs(param):
    handler = BaseHandler(**{param: 'EXAMPLE'})
    assert hasattr(handler, param) and getattr(handler, param) == 'EXAMPLE'


@pytest.mark.parametrize('params', [
    {
        'LOG_AGGREGATOR_HOST': 'https://server.invalid',
        'LOG_AGGREGATOR_PORT': 22222,
        'LOG_AGGREGATOR_TYPE': 'loggly',
        'LOG_AGGREGATOR_USERNAME': 'foo',
        'LOG_AGGREGATOR_PASSWORD': 'bar',
        'LOG_AGGREGATOR_INDIVIDUAL_FACTS': True,
        'LOG_AGGREGATOR_TCP_TIMEOUT': 96,
        'LOG_AGGREGATOR_VERIFY_CERT': False,
        'LOG_AGGREGATOR_PROTOCOL': 'https'
    },
    {
        'LOG_AGGREGATOR_HOST': 'https://server.invalid',
        'LOG_AGGREGATOR_PORT': 22222,
        'LOG_AGGREGATOR_PROTOCOL': 'udp'
    }
])
def test_real_handler_from_django_settings(params):
    settings = LazySettings()
    settings.configure(**params)
    handler = AWXProxyHandler().get_handler(custom_settings=settings)
    # need the _reverse_ dictionary from PARAM_NAMES
    attr_lookup = {}
    for attr_name, setting_name in PARAM_NAMES.items():
        attr_lookup[setting_name] = attr_name
    for setting_name, val in params.items():
        attr_name = attr_lookup[setting_name]
        if attr_name == 'protocol':
            continue
        assert hasattr(handler, attr_name)


def test_invalid_kwarg_to_real_handler():
    settings = LazySettings()
    settings.configure(**{
        'LOG_AGGREGATOR_HOST': 'https://server.invalid',
        'LOG_AGGREGATOR_PORT': 22222,
        'LOG_AGGREGATOR_PROTOCOL': 'udp',
        'LOG_AGGREGATOR_VERIFY_CERT': False  # setting not valid for UDP handler
    })
    handler = AWXProxyHandler().get_handler(custom_settings=settings)
    assert not hasattr(handler, 'verify_cert')


def test_protocol_not_specified():
    settings = LazySettings()
    settings.configure(**{
        'LOG_AGGREGATOR_HOST': 'https://server.invalid',
        'LOG_AGGREGATOR_PORT': 22222,
        'LOG_AGGREGATOR_PROTOCOL': None  # awx/settings/defaults.py
    })
    handler = AWXProxyHandler().get_handler(custom_settings=settings)
    assert isinstance(handler, logging.NullHandler)


def test_base_logging_handler_emit_system_tracking(dummy_log_record):
    handler = BaseHandler(host='127.0.0.1', indv_facts=True)
    handler.setFormatter(LogstashFormatter())
    dummy_log_record.name = 'awx.analytics.system_tracking'
    dummy_log_record.msg = None
    dummy_log_record.inventory_id = 11
    dummy_log_record.host_name = 'my_lucky_host'
    dummy_log_record.job_id = 777
    dummy_log_record.ansible_facts = {
        "ansible_kernel": "4.4.66-boot2docker",
        "ansible_machine": "x86_64",
        "ansible_swapfree_mb": 4663,
    }
    dummy_log_record.ansible_facts_modified = datetime.datetime.now(tzutc()).isoformat()
    sent_payloads = handler.emit(dummy_log_record)

    assert len(sent_payloads) == 1
    assert sent_payloads[0]['ansible_facts'] == dummy_log_record.ansible_facts
    assert sent_payloads[0]['ansible_facts_modified'] == dummy_log_record.ansible_facts_modified
    assert sent_payloads[0]['level'] == 'INFO'
    assert sent_payloads[0]['logger_name'] == 'awx.analytics.system_tracking'
    assert sent_payloads[0]['job_id'] == dummy_log_record.job_id
    assert sent_payloads[0]['inventory_id'] == dummy_log_record.inventory_id
    assert sent_payloads[0]['host_name'] == dummy_log_record.host_name


@pytest.mark.parametrize('host, port, normalized, hostname_only', [
    ('http://localhost', None, 'http://localhost', False),
    ('http://localhost', 8080, 'http://localhost:8080', False),
    ('https://localhost', 443, 'https://localhost:443', False),
    ('ftp://localhost', 443, 'ftp://localhost:443', False),
    ('https://localhost:550', 443, 'https://localhost:550', False),
    ('https://localhost:yoho/foobar', 443, 'https://localhost:443/foobar', False),
    ('https://localhost:yoho/foobar', None, 'https://localhost:yoho/foobar', False),
    ('http://splunk.server:8088/services/collector/event', 80,
     'http://splunk.server:8088/services/collector/event', False),
    ('http://splunk.server/services/collector/event', 8088,
     'http://splunk.server:8088/services/collector/event', False),
    ('splunk.server:8088/services/collector/event', 80,
     'http://splunk.server:8088/services/collector/event', False),
    ('splunk.server/services/collector/event', 8088,
     'http://splunk.server:8088/services/collector/event', False),
    ('localhost', None, 'http://localhost', False),
    ('localhost', 8080, 'http://localhost:8080', False),
    ('localhost', 4399, 'localhost', True),
    ('tcp://localhost:4399/foo/bar', 4399, 'localhost', True),
])
def test_base_logging_handler_host_format(host, port, normalized, hostname_only):
    handler = BaseHandler(host=host, port=port)
    assert handler._get_host(scheme='http', hostname_only=hostname_only) == normalized


@pytest.mark.parametrize(
    'status, reason, exc',
    [(200, '200 OK', None), (404, 'Not Found', LoggingConnectivityException)]
)
@pytest.mark.parametrize('protocol', ['http', 'https', None])
def test_https_logging_handler_connectivity_test(https_adapter, status, reason, exc, protocol):
    host = 'example.org'
    if protocol:
        host = '://'.join([protocol, host])
    https_adapter.status = status
    https_adapter.reason = reason
    settings = LazySettings()
    settings.configure(**{
        'LOG_AGGREGATOR_HOST': host,
        'LOG_AGGREGATOR_PORT': 8080,
        'LOG_AGGREGATOR_TYPE': 'logstash',
        'LOG_AGGREGATOR_USERNAME': 'user',
        'LOG_AGGREGATOR_PASSWORD': 'password',
        'LOG_AGGREGATOR_LOGGERS': ['awx', 'activity_stream', 'job_events', 'system_tracking'],
        'LOG_AGGREGATOR_PROTOCOL': 'https',
        'CLUSTER_HOST_ID': '',
        'LOG_AGGREGATOR_TOWER_UUID': str(uuid4()),
        'LOG_AGGREGATOR_LEVEL': 'DEBUG',
    })

    class FakeHTTPSHandler(HTTPSHandler):

        def __init__(self, *args, **kwargs):
            super(FakeHTTPSHandler, self).__init__(*args, **kwargs)
            self.session.mount('{}://'.format(protocol or 'https'), https_adapter)

        def emit(self, record):
            return super(FakeHTTPSHandler, self).emit(record)

    with mock.patch.object(AWXProxyHandler, 'get_handler_class') as mock_get_class:
        mock_get_class.return_value = FakeHTTPSHandler
        if exc:
            with pytest.raises(exc) as e:
                AWXProxyHandler().perform_test(settings)
            assert str(e).endswith('%s: %s' % (status, reason))
        else:
            assert AWXProxyHandler().perform_test(settings) is None


def test_https_logging_handler_logstash_auth_info():
    handler = HTTPSHandler(message_type='logstash', username='bob', password='ansible')
    handler._add_auth_information()
    assert isinstance(handler.session.auth, requests.auth.HTTPBasicAuth)
    assert handler.session.auth.username == 'bob'
    assert handler.session.auth.password == 'ansible'


def test_https_logging_handler_splunk_auth_info():
    handler = HTTPSHandler(message_type='splunk', password='ansible')
    handler._add_auth_information()
    assert handler.session.headers['Authorization'] == 'Splunk ansible'
    assert handler.session.headers['Content-Type'] == 'application/json'


def test_https_logging_handler_connection_error(connection_error_adapter,
                                                dummy_log_record):
    handler = HTTPSHandler(host='127.0.0.1', message_type='logstash')
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', connection_error_adapter)

    buff = StringIO()
    logging.getLogger('awx.main.utils.handlers').addHandler(
        logging.StreamHandler(buff)
    )

    async_futures = handler.emit(dummy_log_record)
    with pytest.raises(requests.exceptions.ConnectionError):
        [future.result() for future in async_futures]
    assert 'failed to emit log to external aggregator\nTraceback' in buff.getvalue()

    # we should only log failures *periodically*, so causing *another*
    # immediate failure shouldn't report a second ConnectionError
    buff.truncate(0)
    async_futures = handler.emit(dummy_log_record)
    with pytest.raises(requests.exceptions.ConnectionError):
        [future.result() for future in async_futures]
    assert buff.getvalue() == ''


@pytest.mark.parametrize('message_type', ['logstash', 'splunk'])
def test_https_logging_handler_emit_without_cred(https_adapter, dummy_log_record,
                                                 message_type):
    handler = HTTPSHandler(host='127.0.0.1', message_type=message_type)
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('https://', https_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(https_adapter.requests) == 1
    request = https_adapter.requests[0]
    assert request.url == 'https://127.0.0.1/'
    assert request.method == 'POST'

    if message_type == 'logstash':
        # A username + password weren't used, so this header should be missing
        assert 'Authorization' not in request.headers

    if message_type == 'splunk':
        assert request.headers['Authorization'] == 'Splunk None'


def test_https_logging_handler_emit_logstash_with_creds(https_adapter,
                                                        dummy_log_record):
    handler = HTTPSHandler(host='127.0.0.1',
                           username='user', password='pass',
                           message_type='logstash')
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('https://', https_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(https_adapter.requests) == 1
    request = https_adapter.requests[0]
    assert request.headers['Authorization'] == 'Basic %s' % smart_str(base64.b64encode(b"user:pass"))


def test_https_logging_handler_emit_splunk_with_creds(https_adapter,
                                                      dummy_log_record):
    handler = HTTPSHandler(host='127.0.0.1',
                           password='pass', message_type='splunk')
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('https://', https_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(https_adapter.requests) == 1
    request = https_adapter.requests[0]
    assert request.headers['Authorization'] == 'Splunk pass'


@pytest.mark.parametrize('payload, encoded_payload', [
    ('foobar', 'foobar'),
    ({'foo': 'bar'}, '{"foo": "bar"}'),
    ({u'测试键': u'测试值'}, '{"测试键": "测试值"}'),
])
def test_encode_payload_for_socket(payload, encoded_payload):
    assert _encode_payload_for_socket(payload).decode('utf-8') == encoded_payload


def test_udp_handler_create_socket_at_init():
    handler = UDPHandler(host='127.0.0.1', port=4399)
    assert hasattr(handler, 'socket')
    assert isinstance(handler.socket, socket.socket)
    assert handler.socket.family == socket.AF_INET
    assert handler.socket.type == socket.SOCK_DGRAM


def test_udp_handler_send(dummy_log_record):
    handler = UDPHandler(host='127.0.0.1', port=4399)
    handler.setFormatter(LogstashFormatter())
    with mock.patch('awx.main.utils.handlers._encode_payload_for_socket', return_value="des") as encode_mock,\
            mock.patch.object(handler, 'socket') as socket_mock:
        handler.emit(dummy_log_record)
        encode_mock.assert_called_once_with(handler.format(dummy_log_record))
        socket_mock.sendto.assert_called_once_with("des", ('127.0.0.1', 4399))


def test_tcp_handler_send(fake_socket, dummy_log_record):
    handler = TCPHandler(host='127.0.0.1', port=4399, tcp_timeout=5)
    handler.setFormatter(LogstashFormatter())
    with mock.patch('socket.socket', return_value=fake_socket) as sok_init_mock,\
            mock.patch('select.select', return_value=([], [fake_socket], [])):
        handler.emit(dummy_log_record)
        sok_init_mock.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        fake_socket.connect.assert_called_once_with(('127.0.0.1', 4399))
        fake_socket.setblocking.assert_called_once_with(0)
        fake_socket.send.assert_called_once_with(handler.format(dummy_log_record))
        fake_socket.close.assert_called_once()


def test_tcp_handler_return_if_socket_unavailable(fake_socket, dummy_log_record):
    handler = TCPHandler(host='127.0.0.1', port=4399, tcp_timeout=5)
    handler.setFormatter(LogstashFormatter())
    with mock.patch('socket.socket', return_value=fake_socket) as sok_init_mock,\
            mock.patch('select.select', return_value=([], [], [])):
        handler.emit(dummy_log_record)
        sok_init_mock.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        fake_socket.connect.assert_called_once_with(('127.0.0.1', 4399))
        fake_socket.setblocking.assert_called_once_with(0)
        assert not fake_socket.send.called
        fake_socket.close.assert_called_once()


def test_tcp_handler_log_exception(fake_socket, dummy_log_record):
    handler = TCPHandler(host='127.0.0.1', port=4399, tcp_timeout=5)
    handler.setFormatter(LogstashFormatter())
    with mock.patch('socket.socket', return_value=fake_socket) as sok_init_mock,\
            mock.patch('select.select', return_value=([], [], [])),\
            mock.patch('awx.main.utils.handlers.logger') as logger_mock:
        fake_socket.connect.side_effect = Exception("foo")
        handler.emit(dummy_log_record)
        sok_init_mock.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        logger_mock.exception.assert_called_once()
        fake_socket.close.assert_called_once()
        assert not fake_socket.send.called
