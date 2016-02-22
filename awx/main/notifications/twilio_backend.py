# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from twilio.rest import TwilioRestClient

from awx.main.notifications.base import TowerBaseEmailBackend

logger = logging.getLogger('awx.main.notifications.twilio_backend')

class TwilioBackend(TowerBaseEmailBackend):

    init_parameters = {"account_sid": {"label": "Account SID", "type": "string"},
                       "account_token": {"label": "Account Token", "type": "password"},
                       "from_number": {"label": "Source Phone Number", "type": "string"},
                       "to_numbers": {"label": "Destination SMS Numbers", "type": "list"}}
    recipient_parameter = "to_numbers"
    sender_parameter = "from_number"

    def __init__(self, account_sid, account_token, from_phone, fail_silently=False, **kwargs):
        super(TwilioBackend, self).__init__(fail_silently=fail_silently)
        self.account_sid = account_sid
        self.account_token = account_token
        self.from_phone = from_phone

    def send_messages(self, messages):
        sent_messages = 0
        try:
            connection = TwilioRestClient(self.account_sid, self.account_token)
        except Exception as e:
            if not self.fail_silently:
                raise
            logger.error("Exception connecting to Twilio: {}".format(e))

        for m in messages:
            try:
                connection.messages.create(
                    to=m.to,
                    from_=m.from_email,
                    body=m.subject)
                sent_messages += 1
            except Exception as e:
                logger.error("Exception sending messages: {}".format(e))
                if not self.fail_silently:
                    raise
        return sent_messages
