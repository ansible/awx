# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from django.core.mail.backends.smtp import EmailBackend

class CustomEmailBackend(EmailBackend):

    init_parameters = {"host": {"label": "Host", "type": "string"},
                       "port": {"label": "Port", "type": "int"},
                       "username": {"label": "Username", "type": "string"},
                       "password": {"label": "Password", "type": "password"},
                       "use_tls": {"label": "Use TLS", "type": "bool"},
                       "use_ssl": {"label": "Use SSL", "type": "bool"}}

