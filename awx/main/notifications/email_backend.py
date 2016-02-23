# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from django.utils.encoding import smart_text
from django.core.mail.backends.smtp import EmailBackend

class CustomEmailBackend(EmailBackend):

    init_parameters = {"host": {"label": "Host", "type": "string"},
                       "port": {"label": "Port", "type": "int"},
                       "username": {"label": "Username", "type": "string"},
                       "password": {"label": "Password", "type": "password"},
                       "use_tls": {"label": "Use TLS", "type": "bool"},
                       "use_ssl": {"label": "Use SSL", "type": "bool"},
                       "sender": {"label": "Sender Email", "type": "string"},
                       "recipients": {"label": "Recipient List", "type": "list"}}
    recipient_parameter = "recipients"
    sender_parameter = "sender"

    def format_body(self, body):
        body_actual = smart_text("{} #{} had status {} on Ansible Tower, view details at {}\n\n".format(body['friendly_name'],
                                                                                                        body['id'],
                                                                                                        body['status'],
                                                                                                        body['url']))
        body_actual += pprint.pformat(body, indent=4)
        return body_actual
