# -*- coding: utf-8 -*-
import base64
import cStringIO
import json
import logging
import socket
import datetime
from dateutil.tz import tzutc
from uuid import uuid4

import mock

from django.conf import settings
from django.conf import LazySettings
import pytest
import requests
from requests_futures.sessions import FuturesSession

from awx.main.utils.handlers import (BaseHandler, BaseHTTPSHandler as HTTPSHandler,
                                     TCPHandler, UDPHandler, _encode_payload_for_socket,
                                     PARAM_NAMES, LoggingConnectivityException)
from awx.main.utils.formatters import LogstashFormatter


@pytest.fixture()
def dummy_log_record():
    return logging.LogRecord(
        'awx', # logger name
        20, # loglevel INFO
        './awx/some/module.py', # pathname
        100, # lineno
        'User joe logged in', # msg
        tuple(), # args,
        None # exc_info
    )


@pytest.fixture()
def http_adapter():
    class FakeHTTPAdapter(requests.adapters.HTTPAdapter):
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

    return FakeHTTPAdapter()


@pytest.fixture()
def connection_error_adapter():
    class ConnectionErrorAdapter(requests.adapters.HTTPAdapter):

        def send(self, request, **kwargs):
            err = requests.packages.urllib3.exceptions.SSLError()
            raise requests.exceptions.ConnectionError(err, request=request)

    return ConnectionErrorAdapter()


@pytest.fixture
def fake_socket(tmpdir_factory, request):
    sok = socket._socketobject
    sok.send = mock.MagicMock()
    sok.connect = mock.MagicMock()
    sok.setblocking = mock.MagicMock()
    sok.close = mock.MagicMock()
    return sok


def test_https_logging_handler_requests_async_implementation():
    handler = HTTPSHandler()
    assert isinstance(handler.session, FuturesSession)


def test_https_logging_handler_has_default_http_timeout():
    handler = HTTPSHandler.from_django_settings(settings)
    assert handler.tcp_timeout == 5


@pytest.mark.parametrize('param', PARAM_NAMES.keys())
def test_base_logging_handler_defaults(param):
    handler = BaseHandler()
    assert hasattr(handler, param) and getattr(handler, param) is None


@pytest.mark.parametrize('param', PARAM_NAMES.keys())
def test_base_logging_handler_kwargs(param):
    handler = BaseHandler(**{param: 'EXAMPLE'})
    assert hasattr(handler, param) and getattr(handler, param) == 'EXAMPLE'


@pytest.mark.parametrize('param, django_settings_name', PARAM_NAMES.items())
def test_base_logging_handler_from_django_settings(param, django_settings_name):
    settings = LazySettings()
    settings.configure(**{
        django_settings_name: 'EXAMPLE'
    })
    handler = BaseHandler.from_django_settings(settings)
    assert hasattr(handler, param) and getattr(handler, param) == 'EXAMPLE'


@pytest.mark.parametrize('params, logger_name, expected', [
    # skip all records if enabled_flag = False
    ({'enabled_flag': False}, 'awx.main', True),
    # skip all records if the host is undefined
    ({'host': '', 'enabled_flag': True}, 'awx.main', True),
    # skip all records if underlying logger is used by handlers themselves
    ({'host': '127.0.0.1', 'enabled_flag': True}, 'awx.main.utils.handlers', True),
    ({'host': '127.0.0.1', 'enabled_flag': True}, 'awx.main', False),
    ({'host': '127.0.0.1', 'enabled_flag': True, 'enabled_loggers': ['abc']}, 'awx.analytics.xyz', True),
    ({'host': '127.0.0.1', 'enabled_flag': True, 'enabled_loggers': ['xyz']}, 'awx.analytics.xyz', False),
])
def test_base_logging_handler_skip_log(params, logger_name, expected):
    handler = BaseHandler(**params)
    assert handler._skip_log(logger_name) is expected


def test_base_logging_handler_emit(dummy_log_record):
    handler = BaseHandler(host='127.0.0.1', enabled_flag=True,
                          message_type='logstash', lvl='INFO',
                          enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    sent_payloads = handler.emit(dummy_log_record)

    assert len(sent_payloads) == 1
    body = json.loads(sent_payloads[0])

    assert body['level'] == 'INFO'
    assert body['logger_name'] == 'awx'
    assert body['message'] == 'User joe logged in'


def test_base_logging_handler_ignore_low_severity_msg(dummy_log_record):
    handler = BaseHandler(host='127.0.0.1', enabled_flag=True,
                          message_type='logstash', lvl='WARNING',
                          enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    sent_payloads = handler.emit(dummy_log_record)
    assert len(sent_payloads) == 0


def test_base_logging_handler_emit_system_tracking():
    handler = BaseHandler(host='127.0.0.1', enabled_flag=True,
                          message_type='logstash', indv_facts=True, lvl='INFO',
                          enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    record = logging.LogRecord(
        'awx.analytics.system_tracking', # logger name
        20, # loglevel INFO
        './awx/some/module.py', # pathname
        100, # lineno
        None, # msg
        tuple(), # args,
        None # exc_info
    )
    record.inventory_id = 11
    record.host_name = 'my_lucky_host'
    record.ansible_facts = {
        "ansible_kernel": "4.4.66-boot2docker",
        "ansible_machine": "x86_64",
        "ansible_swapfree_mb": 4663,
    }
    record.ansible_facts_modified = datetime.datetime.now(tzutc()).isoformat()
    sent_payloads = handler.emit(record)

    assert len(sent_payloads) == 1
    assert sent_payloads[0]['ansible_facts'] == record.ansible_facts
    assert sent_payloads[0]['level'] == 'INFO'
    assert sent_payloads[0]['logger_name'] == 'awx.analytics.system_tracking'


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
def test_https_logging_handler_connectivity_test(http_adapter, status, reason, exc):
    http_adapter.status = status
    http_adapter.reason = reason
    settings = LazySettings()
    settings.configure(**{
        'LOG_AGGREGATOR_HOST': 'example.org',
        'LOG_AGGREGATOR_PORT': 8080,
        'LOG_AGGREGATOR_TYPE': 'logstash',
        'LOG_AGGREGATOR_USERNAME': 'user',
        'LOG_AGGREGATOR_PASSWORD': 'password',
        'LOG_AGGREGATOR_LOGGERS': ['awx', 'activity_stream', 'job_events', 'system_tracking'],
        'CLUSTER_HOST_ID': '',
        'LOG_AGGREGATOR_TOWER_UUID': str(uuid4()),
        'LOG_AGGREGATOR_LEVEL': 'DEBUG',
    })

    class FakeHTTPSHandler(HTTPSHandler):

        def __init__(self, *args, **kwargs):
            super(FakeHTTPSHandler, self).__init__(*args, **kwargs)
            self.session.mount('http://', http_adapter)

        def emit(self, record):
            return super(FakeHTTPSHandler, self).emit(record)

    if exc:
        with pytest.raises(exc) as e:
            FakeHTTPSHandler.perform_test(settings)
        assert str(e).endswith('%s: %s' % (status, reason))
    else:
        assert FakeHTTPSHandler.perform_test(settings) is None


def test_https_logging_handler_logstash_auth_info():
    handler = HTTPSHandler(message_type='logstash', username='bob', password='ansible', lvl='INFO')
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
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type='logstash', lvl='INFO',
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', connection_error_adapter)

    buff = cStringIO.StringIO()
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
def test_https_logging_handler_emit_without_cred(http_adapter, dummy_log_record,
                                                 message_type):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type=message_type, lvl='INFO',
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', http_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(http_adapter.requests) == 1
    request = http_adapter.requests[0]
    assert request.url == 'http://127.0.0.1/'
    assert request.method == 'POST'

    if message_type == 'logstash':
        # A username + password weren't used, so this header should be missing
        assert 'Authorization' not in request.headers

    if message_type == 'splunk':
        assert request.headers['Authorization'] == 'Splunk None'


def test_https_logging_handler_emit_logstash_with_creds(http_adapter,
                                                        dummy_log_record):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           username='user', password='pass',
                           message_type='logstash', lvl='INFO',
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', http_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(http_adapter.requests) == 1
    request = http_adapter.requests[0]
    assert request.headers['Authorization'] == 'Basic %s' % base64.b64encode("user:pass")


def test_https_logging_handler_emit_splunk_with_creds(http_adapter,
                                                      dummy_log_record):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           password='pass', message_type='splunk', lvl='INFO',
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', http_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(http_adapter.requests) == 1
    request = http_adapter.requests[0]
    assert request.headers['Authorization'] == 'Splunk pass'


@pytest.mark.parametrize('payload, encoded_payload', [
    ('foobar', 'foobar'),
    ({'foo': 'bar'}, '{"foo": "bar"}'),
    ({u'测试键': u'测试值'}, '{"测试键": "测试值"}'),
])
def test_encode_payload_for_socket(payload, encoded_payload):
    assert _encode_payload_for_socket(payload) == encoded_payload


def test_udp_handler_create_socket_at_init():
    handler = UDPHandler(host='127.0.0.1', port=4399,
                         enabled_flag=True, message_type='splunk', lvl='INFO',
                         enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    assert hasattr(handler, 'socket')
    assert isinstance(handler.socket, socket.socket)
    assert handler.socket.family == socket.AF_INET
    assert handler.socket.type == socket.SOCK_DGRAM


def test_udp_handler_send(dummy_log_record):
    handler = UDPHandler(host='127.0.0.1', port=4399,
                         enabled_flag=True, message_type='splunk', lvl='INFO',
                         enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    with mock.patch('awx.main.utils.handlers._encode_payload_for_socket', return_value="des") as encode_mock,\
            mock.patch.object(handler, 'socket') as socket_mock:
        handler.emit(dummy_log_record)
        encode_mock.assert_called_once_with(handler.format(dummy_log_record))
        socket_mock.sendto.assert_called_once_with("des", ('127.0.0.1', 4399))


def test_tcp_handler_send(fake_socket, dummy_log_record):
    handler = TCPHandler(host='127.0.0.1', port=4399, tcp_timeout=5,
                         enabled_flag=True, message_type='splunk', lvl='INFO',
                         enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
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
    handler = TCPHandler(host='127.0.0.1', port=4399, tcp_timeout=5,
                         enabled_flag=True, message_type='splunk', lvl='INFO',
                         enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
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
    handler = TCPHandler(host='127.0.0.1', port=4399, tcp_timeout=5,
                         enabled_flag=True, message_type='splunk', lvl='INFO',
                         enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
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
