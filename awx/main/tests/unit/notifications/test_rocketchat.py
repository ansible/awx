import json

from unittest import mock
from django.core.mail.message import EmailMessage

import awx.main.notifications.rocketchat_backend as rocketchat_backend


def test_send_messages():
    with mock.patch('awx.main.notifications.rocketchat_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 201
        backend = rocketchat_backend.RocketChatBackend()
        message = EmailMessage('test subject', 'test body', [], ['http://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with('http://example.com', data='{"text": "test subject"}', verify=True)
        assert sent_messages == 1


def test_send_messages_with_username():
    with mock.patch('awx.main.notifications.rocketchat_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 201
        backend = rocketchat_backend.RocketChatBackend(rocketchat_username='testuser')
        message = EmailMessage('test subject', 'test body', [], ['http://example.com', ])
        sent_messages = backend.send_messages([message, ])

        calls = requests_mock.post.call_args_list
        assert len(calls) == 1
        args, kwargs = calls[0]
        assert args[0] == 'http://example.com'
        assert json.loads(kwargs['data'])['text'] == 'test subject'
        assert json.loads(kwargs['data'])['username'] == 'testuser'
        assert kwargs['verify'] is True
        assert sent_messages == 1


def test_send_messages_with_icon_url():
    with mock.patch('awx.main.notifications.rocketchat_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 201
        backend = rocketchat_backend.RocketChatBackend(rocketchat_icon_url='http://example.com')
        message = EmailMessage('test subject', 'test body', [], ['http://example.com', ])
        sent_messages = backend.send_messages([message, ])

        calls = requests_mock.post.call_args_list
        assert len(calls) == 1
        args, kwargs = calls[0]
        assert args[0] == 'http://example.com'
        assert json.loads(kwargs['data'])['text'] == 'test subject'
        assert json.loads(kwargs['data'])['icon_url'] == 'http://example.com'
        assert kwargs['verify'] is True
        assert sent_messages == 1


def test_send_messages_with_no_verify_ssl():
    with mock.patch('awx.main.notifications.rocketchat_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 201
        backend = rocketchat_backend.RocketChatBackend(rocketchat_no_verify_ssl=True)
        message = EmailMessage('test subject', 'test body', [], ['http://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with('http://example.com', data='{"text": "test subject"}', verify=False)
        assert sent_messages == 1
