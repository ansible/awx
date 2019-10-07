# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

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

    DEFAULT_MSG = "{{ job_friendly_name }} #{{ job.id }} '{{ job.name }}' {{ job.status }}: {{ url }}"
    DEFAULT_BODY = smart_text(_("{{ job_friendly_name }} #{{ job.id }} had status {{ job.status }}, view details at {{ url }}\n\n{{ job_summary_dict }}"))
    default_messages = {"started": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
                        "success": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
                        "error": {"message": DEFAULT_MSG, "body": DEFAULT_BODY}}
    recipient_parameter = "recipients"
    sender_parameter = "sender"


    def format_body(self, body):
        # leave body unchanged (expect a string)
        return body
