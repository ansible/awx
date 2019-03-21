# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Python
import base64
import binascii
import re

# Django
from django.utils.translation import ugettext_lazy as _

# Tower
from awx.conf import fields, register


class PendoTrackingStateField(fields.ChoiceField):

    def to_internal_value(self, data):
        # Any false/null values get converted to 'off'.
        if data in fields.NullBooleanField.FALSE_VALUES or data in fields.NullBooleanField.NULL_VALUES:
            return 'off'
        return super(PendoTrackingStateField, self).to_internal_value(data)


class CustomLogoField(fields.CharField):

    CUSTOM_LOGO_RE = re.compile(r'^data:image/(?:png|jpeg|gif);base64,([A-Za-z0-9+/=]+?)$')

    default_error_messages = {
        'invalid_format': _('Invalid format for custom logo. Must be a data URL with a base64-encoded GIF, PNG or JPEG image.'),
        'invalid_data': _('Invalid base64-encoded data in data URL.'),
    }

    def to_internal_value(self, data):
        data = super(CustomLogoField, self).to_internal_value(data)
        match = self.CUSTOM_LOGO_RE.match(data)
        if not match:
            self.fail('invalid_format')
        b64data = match.group(1)
        try:
            base64.b64decode(b64data)
        except (TypeError, binascii.Error):
            self.fail('invalid_data')
        return data
