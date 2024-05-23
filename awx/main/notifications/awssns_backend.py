# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.
import json
import logging

import boto3
from botocore.exceptions import ClientError

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.notifications.custom_notification_base import CustomNotificationBase

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
    default_messages = CustomNotificationBase.job_metadata_messages

    def __init__(self, aws_region, aws_access_key_id, aws_secret_access_key, aws_session_token, fail_silently=False, **kwargs):
        session = boto3.session.Session()
        client_config = {"service_name": 'sns'}
        if aws_region:
            client_config["region_name"] = aws_region
        if aws_secret_access_key:
            client_config["aws_secret_access_key"] = aws_secret_access_key
        if aws_access_key_id:
            client_config["aws_access_key_id"] = aws_access_key_id
        if aws_session_token:
            client_config["aws_session_token"] = aws_session_token
        self.client = session.client(**client_config)
        super(AWSSNSBackend, self).__init__(fail_silently=fail_silently)

    def _sns_publish(self, topic_arn, message):
        self.client.publish(TopicArn=topic_arn, Message=message, MessageAttributes={})

    def format_body(self, body):
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass

        if isinstance(body, dict):
            body = json.dumps(body)
        # convert dict body to json string
        return body

    def send_messages(self, messages):
        sent_messages = 0
        for message in messages:
            sns_topic_arn = str(message.recipients()[0])
            try:
                self._sns_publish(topic_arn=sns_topic_arn, message=message.body)
                sent_messages += 1
            except ClientError as error:
                if not self.fail_silently:
                    raise error

        return sent_messages
