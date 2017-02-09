import base64
import json
import logging

from django.conf import LazySettings
import pytest
import requests
from requests_futures.sessions import FuturesSession

from awx.main.utils.handlers import BaseHTTPSHandler as HTTPSHandler, PARAM_NAMES
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
def ok200_adapter():
    class OK200Adapter(requests.adapters.HTTPAdapter):
        requests = []

        def send(self, request, **kwargs):
            self.requests.append(request)
            resp = requests.models.Response()
            resp.status_code = 200
            resp.raw = '200 OK'
            resp.request = request
            return resp

    return OK200Adapter()


@pytest.mark.parametrize('async, implementation', [
    (True, FuturesSession),
    (True, requests.Session)
])
def test_https_logging_handler_requests_implementation(async, implementation):
    handler = HTTPSHandler(async=async)
    assert isinstance(handler.session, implementation)


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


@pytest.mark.parametrize('message_type, async', [
    ('logstash', False),
    ('logstash', True),
    ('splunk', False),
    ('splunk', True),
])
def test_https_logging_handler_emit(ok200_adapter, dummy_log_record,
                                    message_type, async):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type=message_type,
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'],
                           async=async)
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', ok200_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(ok200_adapter.requests) == 1
    request = ok200_adapter.requests[0]
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


@pytest.mark.parametrize('async', (True, False))
def test_https_logging_handler_emit_logstash_with_creds(ok200_adapter,
                                                        dummy_log_record, async):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           username='user', password='pass',
                           message_type='logstash',
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'],
                           async=async)
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', ok200_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(ok200_adapter.requests) == 1
    request = ok200_adapter.requests[0]
    assert request.headers['Authorization'] == 'Basic %s' % base64.b64encode("user:pass")


@pytest.mark.parametrize('async', (True, False))
def test_https_logging_handler_emit_splunk_with_creds(ok200_adapter,
                                                      dummy_log_record, async):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           password='pass', message_type='splunk',
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'],
                           async=async)
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', ok200_adapter)
    async_futures = handler.emit(dummy_log_record)
    [future.result() for future in async_futures]

    assert len(ok200_adapter.requests) == 1
    request = ok200_adapter.requests[0]
    assert request.headers['Authorization'] == 'Splunk pass'


def test_https_logging_handler_emit_one_record_per_fact(ok200_adapter):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type='logstash', indv_facts=True,
                           enabled_loggers=['awx', 'activity_stream', 'job_events', 'system_tracking'])
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', ok200_adapter)
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

    assert len(ok200_adapter.requests) == 2

    request = ok200_adapter.requests[0]
    assert request.url == 'http://127.0.0.1/'
    assert request.method == 'POST'
    body = json.loads(request.body)
    assert body['level'] == 'INFO'
    assert body['logger_name'] == 'awx.analytics.system_tracking'
    assert body['name'] == 'ansible'
    assert body['version'] == '2.2.1.0'

    request = ok200_adapter.requests[1]
    assert request.url == 'http://127.0.0.1/'
    assert request.method == 'POST'
    body = json.loads(request.body)
    assert body['level'] == 'INFO'
    assert body['logger_name'] == 'awx.analytics.system_tracking'
    assert body['name'] == 'ansible-tower'
    assert body['version'] == '3.1.0'
