# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import pprint

from django.utils.encoding import smart_text
from django.core.mail.backends.base import BaseEmailBackend

class TowerBaseEmailBackend(BaseEmailBackend):

    def format_body(self, body):
        if "body" in body:
            body_actual = body['body']
        else:
            body_actual = smart_text("{} #{} had status {} on Ansible Tower, view details at {}\n\n".format(body['friendly_name'],
                                                                                                            body['id'],
                                                                                                            body['status'],
                                                                                                            body['url']))
            body_actual += pprint.pformat(body, indent=4)
        return body_actual
