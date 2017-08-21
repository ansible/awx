# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.utils.translation import ugettext_lazy as _

# Tower
from awx.conf import register, fields
from awx.ui.fields import *  # noqa


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

register(
    'CUSTOM_LOGIN_INFO',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    label=_('Custom Login Info'),
    help_text=_('If needed, you can add specific information (such as a legal '
                'notice or a disclaimer) to a text box in the login modal using '
                'this setting. Any content added must be in plain text, as '
                'custom HTML or other markup languages are not supported.'),
    category=_('UI'),
    category_slug='ui',
    feature_required='rebranding',
)

register(
    'CUSTOM_LOGO',
    field_class=CustomLogoField,
    allow_blank=True,
    default='',
    label=_('Custom Logo'),
    help_text=_('To set up a custom logo, provide a file that you create. For '
                'the custom logo to look its best, use a .png file with a '
                'transparent background. GIF, PNG and JPEG formats are supported.'),
    placeholder='data:image/gif;base64,R0lGODlhAQABAIABAP///wAAACwAAAAAAQABAAACAkQBADs=',
    category=_('UI'),
    category_slug='ui',
    feature_required='rebranding',
)
