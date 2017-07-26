# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import json

from django.utils.encoding import smart_text
from django.core.mail.backends.base import BaseEmailBackend
from django.utils.translation import ugettext_lazy as _


class AWXBaseEmailBackend(BaseEmailBackend):

    def format_body(self, body):
        if "body" in body:
            body_actual = body['body']
        else:
            body_actual = smart_text(_("{} #{} had status {}, view details at {}\n\n").format(
                body['friendly_name'], body['id'], body['status'], body['url'])
            )
            body_actual += json.dumps(body, indent=4)
        return body_actual
