from unittest import mock

from django.core.mail.message import EmailMessage

import awx.main.notifications.pagerduty_backend as pagerduty_backend


def test_send_messages():
    with mock.patch('awx.main.notifications.pagerduty_backend.EventsApiV2Client') as client_mock:
        client = client_mock.return_value
        client.trigger.return_value = 'dedup-key'

        message = EmailMessage(
            'test subject',
            'test body',
            'client@example.com',
            ['service-key'],
        )
        backend = pagerduty_backend.PagerDutyBackend('legacy-subdomain', 'legacy-token')

        sent_messages = backend.send_messages([message])

        client_mock.assert_called_once_with('service-key')
        client.trigger.assert_called_once_with(
            summary='test subject',
            source='client@example.com',
            custom_details={'body': 'test body'},
        )
        assert sent_messages == 1


def test_send_messages_with_json_body():
    with mock.patch('awx.main.notifications.pagerduty_backend.EventsApiV2Client') as client_mock:
        client = client_mock.return_value
        client.trigger.return_value = 'dedup-key'

        message = EmailMessage(
            'test subject',
            '{"details": "test body"}',
            'client@example.com',
            ['service-key'],
        )
        backend = pagerduty_backend.PagerDutyBackend('legacy-subdomain', 'legacy-token')

        sent_messages = backend.send_messages([message])

        client.trigger.assert_called_once_with(
            summary='test subject',
            source='client@example.com',
            custom_details={'details': 'test body'},
        )
        assert sent_messages == 1


def test_send_messages_with_connection_error_fail_silently():
    with mock.patch(
        'awx.main.notifications.pagerduty_backend.EventsApiV2Client',
        side_effect=RuntimeError('connection failed'),
    ) as client_mock:
        message = EmailMessage(
            'test subject',
            'test body',
            'client@example.com',
            ['service-key'],
        )
        backend = pagerduty_backend.PagerDutyBackend('legacy-subdomain', 'legacy-token', fail_silently=True)

        assert backend.send_messages([message]) == 0
        client_mock.assert_called_once_with('service-key')


def test_send_messages_with_send_error_fail_silently():
    with mock.patch('awx.main.notifications.pagerduty_backend.EventsApiV2Client') as client_mock:
        client_mock.return_value.trigger.side_effect = RuntimeError('send failed')

        message = EmailMessage(
            'test subject',
            'test body',
            'client@example.com',
            ['service-key'],
        )
        backend = pagerduty_backend.PagerDutyBackend('legacy-subdomain', 'legacy-token', fail_silently=True)

        assert backend.send_messages([message]) == 0
        client_mock.return_value.trigger.assert_called_once_with(
            summary='test subject',
            source='client@example.com',
            custom_details={'body': 'test body'},
        )


def test_format_body_accepts_dict():
    backend = pagerduty_backend.PagerDutyBackend('legacy-subdomain', 'legacy-token')
    body = {'details': 'test body'}

    assert backend.format_body(body) is body
