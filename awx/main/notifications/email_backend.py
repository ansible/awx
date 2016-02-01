# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import logging

from django.core.mail.backends.smtp import EmailBackend

class CustomEmailBackend(EmailBackend):

    init_parameters = ("host", "port", "username", "password",
                       "use_tls", "use_ssl")
