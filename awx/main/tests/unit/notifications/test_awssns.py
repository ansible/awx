from unittest import mock
from django.core.mail.message import EmailMessage

import awx.main.notifications.awssns_backend as awssns_backend


def test_send_messages():
    with mock.patch('awx.main.notifications.awssns_backend.AWSSNSBackend._sns_publish') as sns_publish_mock:
        aws_region = 'us-east-1'
        sns_topic = f"arn:aws:sns:{aws_region}:111111111111:topic-mock"
        backend = awssns_backend.AWSSNSBackend(aws_region=aws_region, aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None)
        message = EmailMessage(
            'test subject',
            {'body': 'test body'},
            [],
            [
                sns_topic,
            ],
        )
        sent_messages = backend.send_messages(
            [
                message,
            ]
        )
        sns_publish_mock.assert_called_once_with(topic_arn=sns_topic, message=message.body)
        assert sent_messages == 1
