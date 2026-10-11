import logging
import re
import uuid

from django.http import HttpResponse
from django.test import RequestFactory

from ansible_base.lib.logging.context import trace_id_var
from ansible_base.lib.middleware.observability import ObservabilityMiddleware

from awx.main.middleware import RequestIdHeaderMiddleware
from awx.main.utils.filters import DefaultCorrelationId


def _stack(seen):
    """RequestIdHeaderMiddleware around django-ansible-base's ObservabilityMiddleware, as in MIDDLEWARE."""

    def view(request):
        seen.append(trace_id_var.get())
        return HttpResponse('ok')

    return RequestIdHeaderMiddleware(ObservabilityMiddleware(view))


def test_every_response_names_the_request_under_both_headers_and_exposes_them():
    seen = []
    response = _stack(seen)(RequestFactory().get('/api/v2/ping/'))
    request_id = response['X-Request-ID']
    uuid.UUID(request_id)
    assert response['X-API-Request-Id'] == request_id
    assert seen == [request_id]  # the id log records carry while the request runs
    assert trace_id_var.get() is None  # and it does not leak past the request
    exposed = {h.strip() for h in response['Access-Control-Expose-Headers'].split(',')}
    assert {'X-Request-ID', 'X-API-Request-Id'} <= exposed
    assert re.fullmatch(r'\d+\.\d{3}s', response['X-API-Total-Time'])


def test_a_client_x_api_request_id_names_the_request():
    given = str(uuid.uuid4())
    seen = []
    response = _stack(seen)(RequestFactory().get('/api/v2/ping/', HTTP_X_API_REQUEST_ID=given))
    assert response['X-Request-ID'] == response['X-API-Request-Id'] == given == seen[0]


def test_x_request_id_wins_over_the_legacy_header():
    gateway, legacy = str(uuid.uuid4()), str(uuid.uuid4())
    seen = []
    response = _stack(seen)(RequestFactory().get('/', HTTP_X_REQUEST_ID=gateway, HTTP_X_API_REQUEST_ID=legacy))
    assert response['X-Request-ID'] == response['X-API-Request-Id'] == gateway == seen[0]


def test_an_invalid_id_is_replaced():
    seen = []
    response = _stack(seen)(RequestFactory().get('/', HTTP_X_API_REQUEST_ID='not-a-uuid'))
    assert response['X-Request-ID'] != 'not-a-uuid'
    uuid.UUID(response['X-Request-ID'])


def test_log_records_carry_the_trace_id_as_guid():
    record = logging.LogRecord('awx', logging.INFO, __file__, 1, 'hello', None, None)
    token = trace_id_var.set('0b6c3b1e-8a1d-4c1a-9f7e-1d2c3b4a5f60')
    try:
        assert DefaultCorrelationId().filter(record) is True
    finally:
        trace_id_var.reset(token)
    assert record.guid in ('0b6c3b1e-8a1d-4c1a-9f7e-1d2c3b4a5f60', '0b6c3b1e')  # the dev MODE shortens it

    outside = logging.LogRecord('awx', logging.INFO, __file__, 1, 'hello', None, None)
    DefaultCorrelationId().filter(outside)
    assert outside.guid == '-'


def test_a_dispatcher_task_runs_under_the_id_its_message_carries(mocker):
    from awx.main.dispatch.worker import task as task_worker

    seen = []
    mocker.patch.object(task_worker, 'resolve_callable', return_value=lambda *a, **kw: seen.append(trace_id_var.get()))
    token = trace_id_var.set(None)
    try:
        task_worker.run_callable({'task': 'awx.main.tasks.system.noop', 'args': [], 'kwargs': {}, 'guid': 'abc'})
    finally:
        trace_id_var.reset(token)
    assert seen == ['abc']
