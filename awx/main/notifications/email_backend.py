# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import json

from django.utils.encoding import smart_text
from django.core.mail.backends.smtp import EmailBackend
from django.utils.translation import ugettext_lazy as _


class CustomEmailBackend(EmailBackend):

    init_parameters = {"host": {"label": "Host", "type": "string"},
                       "port": {"label": "Port", "type": "int"},
                       "username": {"label": "Username", "type": "string"},
                       "password": {"label": "Password", "type": "password"},
                       "use_tls": {"label": "Use TLS", "type": "bool"},
                       "use_ssl": {"label": "Use SSL", "type": "bool"},
                       "sender": {"label": "Sender Email", "type": "string"},
                       "recipients": {"label": "Recipient List", "type": "list"},
                       "timeout": {"label": "Timeout", "type": "int", "default": 30}}
    recipient_parameter = "recipients"
    sender_parameter = "sender"


    def format_body(self, body):
        if "body" in body:
            body_actual = body['body']
        else:
            body_actual = smart_text(_("{} #{} had status {}, view details at {}\n\n").format(
                body['friendly_name'], body['id'], body['status'], body['url'])
            )
            body_actual += json.dumps(body, indent=4)
        return body_actual
