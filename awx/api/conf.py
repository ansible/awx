# Django
from django.utils.translation import ugettext_lazy as _

# Tower
from awx.conf import fields, register


register(
    'AUTH_TOKEN_EXPIRATION',
    field_class=fields.IntegerField,
    min_value=60,
    label=_('Idle Time Force Log Out'),
    help_text=_('Number of seconds that a user is inactive before they will need to login again.'),
    category=_('Authentication'),
    category_slug='authentication',
)

register(
    'AUTH_TOKEN_PER_USER',
    field_class=fields.IntegerField,
    min_value=-1,
    label=_('Maximum number of simultaneous logins'),
    help_text=_('Maximum number of simultaneous logins a user may have. To disable enter -1.'),
    category=_('Authentication'),
    category_slug='authentication',
)

register(
    'AUTH_BASIC_ENABLED',
    field_class=fields.BooleanField,
    label=_('Enable HTTP Basic Auth'),
    help_text=_('Enable HTTP Basic Auth for the API Browser.'),
    category=_('Authentication'),
    category_slug='authentication',
)
