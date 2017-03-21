import base64
import cStringIO
import json
import logging
from uuid import uuid4

from django.conf import settings
from django.conf import LazySettings
import pytest
import requests
from requests_futures.sessions import FuturesSession

from awx.main.utils.handlers import (BaseHTTPSHandler as HTTPSHandler,
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


def test_https_logging_handler_requests_async_implementation():
    handler = HTTPSHandler()
    assert isinstance(handler.session, FuturesSession)


def test_https_logging_handler_has_default_http_timeout():
    handler = HTTPSHandler.from_django_settings(settings)
    assert handler.http_timeout == 5


@pytest.mark.parametrize('param', PARAM_NAMES.keys())
def test_https_logging_handler_defaults(param):
    handler = HTTPSHandler()
    assert hasattr(handler, param) and getattr(handler, param) is None


@pytest.mark.parametrize('param', PARAM_NAMES.keys())
def test_https_logging_handler_kwargs(param):
    handler = HTTPSHandler(**{param: 'EXAMPLE'})
    assert hasattr(handler, param) and getattr(handler, param) == 'EXAMPLE'


@pytest.mark.parametrize('param, django_settings_name', PARAM_NAMES.items())
def test_https_logging_handler_from_django_settings(param, django_settings_name):
    settings = LazySettings()
    settings.configure(**{
        django_settings_name: 'EXAMPLE'
    })
    handler = HTTPSHandler.from_django_settings(settings)
    assert hasattr(handler, param) and getattr(handler, param) == 'EXAMPLE'


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
        'LOG_AGGREGATOR_TOWER_UUID': str(uuid4())
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
    handler = HTTPSHandler(message_type='logstash', username='bob', password='ansible')
    handler.add_auth_information()
    assert isinstance(handler.session.auth, requests.auth.HTTPBasicAuth)
    assert handler.session.auth.username == 'bob'
    assert handler.session.auth.password == 'ansible'


def test_https_logging_handler_splunk_auth_info():
    handler = HTTPSHandler(message_type='splunk', password='ansible')
    handler.add_auth_information()
    assert handler.session.headers['Authorization'] == 'Splunk ansible'
    assert handler.session.headers['Content-Type'] == 'application/json'


@pytest.mark.parametrize('host, port, normalized', [
    ('localhost', None, 'http://localhost'),
    ('localhost', 80, 'http://localhost'),
    ('localhost', 8080, 'http://localhost:8080'),
    ('http://localhost', None, 'http://localhost'),
    ('http://localhost', 80, 'http://localhost'),
    ('http://localhost', 8080, 'http://localhost:8080'),
    ('https://localhost', 443, 'https://localhost:443')
])
def test_https_logging_handler_http_host_format(host, port, normalized):
    handler = HTTPSHandler(host=host, port=port)
    assert handler.get_http_host() == normalized


@pytest.mark.parametrize('params, logger_name, expected', [
    ({'enabled_flag': False}, 'awx.main', True),  # skip all records if enabled_flag = False
    ({'host': '', 'enabled_flag': True}, 'awx.main', True),  # skip all records if the host is undefined
    ({'host': '127.0.0.1', 'enabled_flag': True}, 'awx.main', False),
    ({'host': '127.0.0.1', 'enabled_flag': True, 'enabled_loggers': ['abc']}, 'awx.analytics.xyz', True),
    ({'host': '127.0.0.1', 'enabled_flag': True, 'enabled_loggers': ['xyz']}, 'awx.analytics.xyz', False),
])
def test_https_logging_handler_skip_log(params, logger_name, expected):
    handler = HTTPSHandler(**params)
    assert handler.skip_log(logger_name) is expected


def test_https_logging_handler_connection_error(connection_error_adapter,
                                                dummy_log_record):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type='logstash',
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
def test_https_logging_handler_emit(http_adapter, dummy_log_record,
                                    message_type):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type=message_type,
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', http_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(http_adapter.requests) == 1
    request = http_adapter.requests[0]
    assert request.url == 'http://127.0.0.1/'
    assert request.method == 'POST'
    body = json.loads(request.body)

    if message_type == 'logstash':
        # A username + password weren't used, so this header should be missing
        assert 'Authorization' not in request.headers

    if message_type == 'splunk':
        # splunk messages are nested under the 'event' key
        body = body['event']
        assert request.headers['Authorization'] == 'Splunk None'

    assert body['level'] == 'INFO'
    assert body['logger_name'] == 'awx'
    assert body['message'] == 'User joe logged in'


def test_https_logging_handler_emit_logstash_with_creds(http_adapter,
                                                        dummy_log_record):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           username='user', password='pass',
                           message_type='logstash',
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
                           password='pass', message_type='splunk',
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', http_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(http_adapter.requests) == 1
    request = http_adapter.requests[0]
    assert request.headers['Authorization'] == 'Splunk pass'


def test_https_logging_handler_emit_one_record_per_fact(http_adapter):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type='logstash', indv_facts=True,
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', http_adapter)
    record = logging.LogRecord(
        'awx.analytics.system_tracking', # logger name
        20, # loglevel INFO
        './awx/some/module.py', # pathname
        100, # lineno
        None, # msg
        tuple(), # args,
        None # exc_info
    )
    record.module_name = 'packages'
    record.facts_data = [{
        "name": "ansible",
        "version": "2.2.1.0"
    }, {
        "name": "ansible-tower",
        "version": "3.1.0"
    }]
    async_futures = handler.emit(record)
    [future.result() for future in async_futures]

    assert len(http_adapter.requests) == 2
    requests = sorted(http_adapter.requests, key=lambda request: json.loads(request.body)['version'])

    request = requests[0]
    assert request.url == 'http://127.0.0.1/'
    assert request.method == 'POST'
    body = json.loads(request.body)
    assert body['level'] == 'INFO'
    assert body['logger_name'] == 'awx.analytics.system_tracking'
    assert body['name'] == 'ansible'
    assert body['version'] == '2.2.1.0'

    request = requests[1]
    assert request.url == 'http://127.0.0.1/'
    assert request.method == 'POST'
    body = json.loads(request.body)
    assert body['level'] == 'INFO'
    assert body['logger_name'] == 'awx.analytics.system_tracking'
    assert body['name'] == 'ansible-tower'
    assert body['version'] == '3.1.0'
