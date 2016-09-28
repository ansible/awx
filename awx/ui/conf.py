# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.utils.translation import ugettext_lazy as _

# Tower
from awx.conf import fields, register


register(
    'PENDO_TRACKING_STATE',
    field_class=fields.ChoiceField,
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
