import json

from unittest import mock
from django.core.mail.message import EmailMessage

import awx.main.notifications.webhook_backend as webhook_backend


def test_send_messages_as_POST():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        requests_mock.post.return_value.status_code = 200
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None)
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        requests_mock.post.assert_called_once_with(
            url='http://example.com',
            auth=None,
            data=json.dumps({'text': 'test body'}, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'},
            verify=True,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_as_PUT():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        requests_mock.put.return_value.status_code = 200
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('PUT', None)
        message = EmailMessage(
            'test subject 2',
            {'text': 'test body 2'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        requests_mock.put.assert_called_once_with(
            url='http://example.com',
            auth=None,
            data=json.dumps({'text': 'test body 2'}, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'},
            verify=True,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_with_username():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        requests_mock.post.return_value.status_code = 200
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None, username='userstring')
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        requests_mock.post.assert_called_once_with(
            url='http://example.com',
            auth=('userstring', None),
            data=json.dumps({'text': 'test body'}, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'},
            verify=True,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_with_password():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        requests_mock.post.return_value.status_code = 200
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None, password='passwordstring')
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        requests_mock.post.assert_called_once_with(
            url='http://example.com',
            auth=(None, 'passwordstring'),
            data=json.dumps({'text': 'test body'}, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'},
            verify=True,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_with_username_and_password():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        requests_mock.post.return_value.status_code = 200
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None, username='userstring', password='passwordstring')
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        requests_mock.post.assert_called_once_with(
            url='http://example.com',
            auth=('userstring', 'passwordstring'),
            data=json.dumps({'text': 'test body'}, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'},
            verify=True,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_with_no_verify_ssl():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        requests_mock.post.return_value.status_code = 200
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None, disable_ssl_verification=True)
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        requests_mock.post.assert_called_once_with(
            url='http://example.com',
            auth=None,
            data=json.dumps({'text': 'test body'}, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'},
            verify=False,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_with_additional_headers():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        requests_mock.post.return_value.status_code = 200
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', {'X-Test-Header1': 'test-content-1', 'X-Test-Header2': 'test-content-2'})
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        requests_mock.post.assert_called_once_with(
            url='http://example.com',
            auth=None,
            data=json.dumps({'text': 'test body'}, ensure_ascii=False).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'AWX 0.0.1.dev (open)',
                'X-Test-Header1': 'test-content-1',
                'X-Test-Header2': 'test-content-2',
            },
            verify=True,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_with_redirects_ok():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock:
        # First two calls return redirects, third call returns 200
        requests_mock.post.side_effect = [
            mock.Mock(status_code=301, headers={"Location": "http://redirect1.com"}),
            mock.Mock(status_code=307, headers={"Location": "http://redirect2.com"}),
            mock.Mock(status_code=200),
        ]
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None)
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        assert requests_mock.post.call_count == 3
        requests_mock.post.assert_called_with(
            url='http://redirect2.com',
            auth=None,
            data=json.dumps({'text': 'test body'}, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'},
            verify=True,
            allow_redirects=False,
        )
        assert sent_messages == 1


def test_send_messages_with_redirects_blank():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock, mock.patch('awx.main.notifications.webhook_backend.logger') as logger_mock:
        # First call returns a redirect with Location header, second call returns 301 but NO Location header
        requests_mock.post.side_effect = [
            mock.Mock(status_code=301, headers={"Location": "http://redirect1.com"}),
            mock.Mock(status_code=301, headers={}),  # 301 with no Location header
        ]
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None, fail_silently=True)
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        # Should make 2 requests (initial + 1 redirect attempt)
        assert requests_mock.post.call_count == 2
        # The error message should be logged
        logger_mock.error.assert_called_once()
        error_call_args = logger_mock.error.call_args[0][0]
        assert "redirect to a blank URL" in error_call_args
        assert sent_messages == 0


def test_send_messages_with_redirects_max_retries_exceeded():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock, mock.patch('awx.main.notifications.webhook_backend.logger') as logger_mock:
        # Return MAX_RETRIES (5) redirect responses to exceed the retry limit
        requests_mock.post.side_effect = [
            mock.Mock(status_code=301, headers={"Location": "http://redirect1.com"}),
            mock.Mock(status_code=301, headers={"Location": "http://redirect2.com"}),
            mock.Mock(status_code=307, headers={"Location": "http://redirect3.com"}),
            mock.Mock(status_code=301, headers={"Location": "http://redirect4.com"}),
            mock.Mock(status_code=307, headers={"Location": "http://redirect5.com"}),
        ]
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None, fail_silently=True)
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        # Should make exactly 5 requests (MAX_RETRIES)
        assert requests_mock.post.call_count == 5
        # The error message should be logged for exceeding max retries
        logger_mock.error.assert_called_once()
        error_call_args = logger_mock.error.call_args[0][0]
        assert "max number of retries" in error_call_args
        assert "[5]" in error_call_args
        assert sent_messages == 0


def test_send_messages_with_error_status_code():
    with mock.patch('awx.main.notifications.webhook_backend.requests') as requests_mock, mock.patch(
        'awx.main.notifications.webhook_backend.get_awx_http_client_headers'
    ) as version_mock, mock.patch('awx.main.notifications.webhook_backend.logger') as logger_mock:
        # Return a 404 error status code
        requests_mock.post.return_value = mock.Mock(status_code=404)
        version_mock.return_value = {'Content-Type': 'application/json', 'User-Agent': 'AWX 0.0.1.dev (open)'}
        backend = webhook_backend.WebhookBackend('POST', None, fail_silently=True)
        message = EmailMessage(
            'test subject',
            {'text': 'test body'},
            [],
            [
                'http://example.com',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        # Should make exactly 1 request
        assert requests_mock.post.call_count == 1
        # The error message should be logged
        logger_mock.error.assert_called_once()
        error_call_args = logger_mock.error.call_args[0][0]
        assert "Error sending webhook notification: 404" in error_call_args
        assert sent_messages == 0
