# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import ipaddress
import logging
import socket

from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend

from awx.main.notifications.custom_notification_base import CustomNotificationBase
from awx.main.notifications.url_validation import _is_always_denied, _is_hostname_allowed, _is_ip_allowed

logger = logging.getLogger('awx.main.notifications.email_backend')

DEFAULT_MSG = CustomNotificationBase.DEFAULT_MSG
DEFAULT_BODY = CustomNotificationBase.DEFAULT_BODY

DEFAULT_APPROVAL_RUNNING_MSG = CustomNotificationBase.DEFAULT_APPROVAL_RUNNING_MSG
DEFAULT_APPROVAL_RUNNING_BODY = CustomNotificationBase.DEFAULT_APPROVAL_RUNNING_BODY

DEFAULT_APPROVAL_APPROVED_MSG = CustomNotificationBase.DEFAULT_APPROVAL_APPROVED_MSG
DEFAULT_APPROVAL_APPROVED_BODY = CustomNotificationBase.DEFAULT_APPROVAL_APPROVED_BODY

DEFAULT_APPROVAL_TIMEOUT_MSG = CustomNotificationBase.DEFAULT_APPROVAL_TIMEOUT_MSG
DEFAULT_APPROVAL_TIMEOUT_BODY = CustomNotificationBase.DEFAULT_APPROVAL_TIMEOUT_BODY

DEFAULT_APPROVAL_DENIED_MSG = CustomNotificationBase.DEFAULT_APPROVAL_DENIED_MSG
DEFAULT_APPROVAL_DENIED_BODY = CustomNotificationBase.DEFAULT_APPROVAL_DENIED_BODY


class CustomEmailBackend(EmailBackend, CustomNotificationBase):
    init_parameters = {
        "host": {"label": "Host", "type": "string"},
        "port": {"label": "Port", "type": "int"},
        "username": {"label": "Username", "type": "string"},
        "password": {"label": "Password", "type": "password"},
        "use_tls": {"label": "Use TLS", "type": "bool"},
        "use_ssl": {"label": "Use SSL", "type": "bool"},
        "sender": {"label": "Sender Email", "type": "string"},
        "recipients": {"label": "Recipient List", "type": "list"},
        "timeout": {"label": "Timeout", "type": "int", "default": 30},
    }
    recipient_parameter = "recipients"
    sender_parameter = "sender"

    default_messages = {
        "started": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
        "success": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
        "error": {"message": DEFAULT_MSG, "body": DEFAULT_BODY},
        "workflow_approval": {
            "running": {"message": DEFAULT_APPROVAL_RUNNING_MSG, "body": DEFAULT_APPROVAL_RUNNING_BODY},
            "approved": {"message": DEFAULT_APPROVAL_APPROVED_MSG, "body": DEFAULT_APPROVAL_APPROVED_BODY},
            "timed_out": {"message": DEFAULT_APPROVAL_TIMEOUT_MSG, "body": DEFAULT_APPROVAL_TIMEOUT_BODY},
            "denied": {"message": DEFAULT_APPROVAL_DENIED_MSG, "body": DEFAULT_APPROVAL_DENIED_BODY},
        },
    }

    def format_body(self, body):
        # leave body unchanged (expect a string)
        return body

    @staticmethod
    def _validate_host_not_internal(host):
        if not host:
            return
        if host.startswith('[') and host.endswith(']'):
            host = host[1:-1]

        allow_list = getattr(settings, 'NOTIFICATION_IP_ALLOW_LIST', [])
        hostname_allowed = _is_hostname_allowed(host, allow_list)

        try:
            addrinfo = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return

        for family, type_, proto, canonname, sockaddr in addrinfo:
            try:
                ip = ipaddress.ip_address(sockaddr[0])
            except ValueError:
                continue
            if _is_always_denied(ip):
                raise ValueError(f'SMTP host {host!r} resolves to link-local address {ip} (always blocked)')
            if not hostname_allowed:
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    if not _is_ip_allowed(ip, allow_list):
                        raise ValueError(f'SMTP host is not allowed: {host!r} resolves to blocked address {ip}')

    def open(self):
        self._validate_host_not_internal(self.host)
        return super().open()
