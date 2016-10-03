# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

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


register(
    'PENDO_TRACKING_STATE',
    field_class=PendoTrackingStateField,
    choices=[
        ('off', _('Off')),
        ('anonymous', _('Anonymous')),
        ('detailed', _('Detailed')),
    ],
    label=_('Analytics Tracking State'),
    help_text=_('Enable or Disable Analytics Tracking.'),
    category=_('UI'),
    category_slug='ui',
)
