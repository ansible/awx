# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.
import json
import logging

import boto3
from botocore.exceptions import ClientError

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.notifications.custom_notification_base import CustomNotificationBase
from awx.main.notifications.webhook_backend import WebhookBackend

logger = logging.getLogger('awx.main.notifications.awssns_backend')
WEBSOCKET_TIMEOUT = 30


class AWSSNSBackend(AWXBaseEmailBackend, CustomNotificationBase):
    init_parameters = {
        "aws_region": {"label": "AWS Region", "type": "string", "default": ""},
        "aws_access_key_id": {"label": "Access Key ID", "type": "string", "default": ""},
        "aws_secret_access_key": {"label": "Secret Access Key", "type": "password", "default": ""},
        "aws_session_token": {"label": "Session Token", "type": "password", "default": ""},
        "sns_topic_arn": {"label": "SNS Topic ARN", "type": "string", "default": ""},
    }
    recipient_parameter = "sns_topic_arn"
    sender_parameter = None

    DEFAULT_BODY = "{{ job_metadata }}"
    default_messages = WebhookBackend.default_messages

    def __init__(self, aws_region, aws_access_key_id, aws_secret_access_key, aws_session_token, fail_silently=False, **kwargs):
        self.aws_region = aws_region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        super(AWSSNSBackend, self).__init__(fail_silently=fail_silently)

    def send_messages(self, messages):
        sent_messages = 0
        session = boto3.session.Session()
        client_config = {"service_name": 'sns'}
        if self.aws_region:
            client_config["region_name"] = self.aws_region
        if self.aws_secret_access_key:
            client_config["aws_secret_access_key"] = self.aws_secret_access_key
        if self.aws_access_key_id:
            client_config["aws_access_key_id"] = self.aws_access_key_id
        if self.aws_session_token:
            client_config["aws_session_token"] = self.aws_session_token
        client = session.client(**client_config)

        for message in messages:
            sns_topic_arn = str(message.recipients()[0])
            try:
                client.publish(TopicArn=sns_topic_arn, Subject=message.subject, Message=json.dumps(message.body), MessageAttributes={})
                sent_messages += 1
            except ClientError as error:
                if not self.fail_silently:
                    raise error

        return sent_messages
