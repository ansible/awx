import pytest

from unittest import mock
from django.core.mail.message import EmailMessage

import awx.main.notifications.slack_backend as slack_backend


def test_send_messages():
    with mock.patch('awx.main.notifications.slack_backend.WebClient') as slack_sdk_mock:
        WebClient_mock = slack_sdk_mock.return_value
        WebClient_mock.chat_postMessage.return_value = {'ok': True}
        backend = slack_backend.SlackBackend('slack_access_token')
        message = EmailMessage(
            'test subject',
            'test body',
            [],
            [
                '#random',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        WebClient_mock.chat_postMessage.assert_called_once_with(channel='random', thread_ts=None, as_user=True, text='test subject')
        assert sent_messages == 1


def test_send_messages_with_color():
    with mock.patch('awx.main.notifications.slack_backend.WebClient') as slack_sdk_mock:
        WebClient_mock = slack_sdk_mock.return_value
        WebClient_mock.chat_postMessage.return_value = {'ok': True}
        backend = slack_backend.SlackBackend('slack_access_token', hex_color='#006699')
        message = EmailMessage(
            'test subject',
            'test body',
            [],
            [
                '#random',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )

        WebClient_mock.chat_postMessage.assert_called_once_with(
            channel='random', as_user=True, thread_ts=None, attachments=[{'color': '#006699', 'text': 'test subject'}]
        )
        assert sent_messages == 1


def test_send_messages_fail():
    with mock.patch('awx.main.notifications.slack_backend.WebClient') as slack_sdk_mock, pytest.raises(RuntimeError, match=r'.*not_in_channel.*'):
        WebClient_mock = slack_sdk_mock.return_value
        WebClient_mock.chat_postMessage.return_value = {'ok': False, 'error': 'not_in_channel'}
        backend = slack_backend.SlackBackend('slack_access_token')
        message = EmailMessage(
            'test subject',
            'test body',
            [],
            [
                '#not_existing',
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        WebClient_mock.chat_postMessage.assert_called_once_with(channel='not_existing', as_user=True, text='test subject')
        assert sent_messages == 0
