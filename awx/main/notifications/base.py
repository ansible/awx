# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from django.core.mail.backends.base import BaseEmailBackend


class AWXBaseEmailBackend(BaseEmailBackend):

    def format_body(self, body):
        return body
