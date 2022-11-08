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
