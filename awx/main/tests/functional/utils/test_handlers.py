import json
import logging

import pytest
import requests

from awx.main.utils.handlers import HTTPSHandler
from awx.main.utils.formatters import LogstashFormatter


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



@pytest.mark.django_db
@pytest.mark.parametrize('param, value', [
    ('host', None),
    ('port', None),
    ('message_type', None),
    ('username', None),
    ('password', None),
    ('enabled_loggers', ['awx', 'activity_stream', 'job_events', 'system_tracking']),
    ('indv_facts', None),
    ('enabled_flag', None)
])
def test_https_logging_handler_defaults(param, value):
    handler = HTTPSHandler()
    assert hasattr(handler, param) and getattr(handler, param) == value


@pytest.mark.django_db
@pytest.mark.parametrize('param', ['host', 'port', 'message_type', 'username',
                                   'password', 'indv_facts', 'enabled_flag'])
def test_https_logging_handler_kwargs(param):
    handler = HTTPSHandler(**{param: 'EXAMPLE'})
    assert hasattr(handler, param) and getattr(handler, param) == 'EXAMPLE'


@pytest.mark.django_db
def test_https_logging_handler_logstash_auth_info():
    handler = HTTPSHandler(message_type='logstash', username='bob', password='ansible')
    handler.add_auth_information()
    assert isinstance(handler.session.auth, requests.auth.HTTPBasicAuth)
    assert handler.session.auth.username == 'bob'
    assert handler.session.auth.password == 'ansible'


@pytest.mark.django_db
def test_https_logging_handler_splunk_auth_info():
    handler = HTTPSHandler(message_type='splunk', password='ansible')
    handler.add_auth_information()
    assert handler.session.headers['Authorization'] == 'Splunk ansible'
    assert handler.session.headers['Content-Type'] == 'application/json'


@pytest.mark.django_db
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


@pytest.mark.django_db
@pytest.mark.parametrize('params, logger_name, expected', [
    ({'enabled_flag': False}, 'awx.main', True),  # skip all records if enabled_flag = False
    ({'host': '', 'enabled_flag': True}, 'awx.main', True),  # skip all records if the host is undefined
    ({'host': '127.0.0.1', 'enabled_flag': True}, 'awx.main', False),
    ({'host': '127.0.0.1', 'enabled_flag': True, 'enabled_loggers': ['abc']}, 'awx.analytics.xyz', True),
    ({'host': '127.0.0.1', 'enabled_flag': True, 'enabled_loggers': ['xyz']}, 'awx.analytics.xyz', False),
])
def test_https_logging_handler_skip_log(params, logger_name, expected):
    handler = HTTPSHandler(**params)
    # override the default loggers set by django_settings
    handler.enabled_loggers = params.get('enabled_loggers')
    assert handler.skip_log(logger_name) is expected


@pytest.mark.django_db
@pytest.mark.parametrize('message_type', ['logstash', 'splunk'])
def test_https_logging_handler_emit(ok200_adapter, message_type):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type=message_type)
    handler.setFormatter(LogstashFormatter())
    handler.session.mount('http://', ok200_adapter)
    record = logging.LogRecord(
        'awx', # logger name
        20, # loglevel INFO
        './awx/some/module.py', # pathname
        100, # lineno
        'User joe logged in', # msg
        tuple(), # args,
        None # exc_info
    )
    async_futures = handler.emit(record)
    [future.result() for future in async_futures]

    assert len(ok200_adapter.requests) == 1
    request = ok200_adapter.requests[0]
    assert request.url == 'http://127.0.0.1/'
    assert request.method == 'POST'
    body = json.loads(request.body)

    if message_type == 'splunk':
        # splunk messages are nested under the 'event' key
        body = body['event']

    assert body['level'] == 'INFO'
    assert body['logger_name'] == 'awx'
    assert body['message'] == 'User joe logged in'


@pytest.mark.django_db
def test_https_logging_handler_emit_one_record_per_fact(ok200_adapter):
    handler = HTTPSHandler(host='127.0.0.1', enabled_flag=True,
                           message_type='logstash', indv_facts=True)
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
