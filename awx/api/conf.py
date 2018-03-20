# Django
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.conf import fields, register
from awx.api.fields import OAuth2ProviderField


register(
    'SESSION_COOKIE_AGE',
    field_class=fields.IntegerField,
    min_value=60,
    label=_('Idle Time Force Log Out'),
    help_text=_('Number of seconds that a user is inactive before they will need to login again.'),
    category=_('Authentication'),
    category_slug='authentication',
)
register(
    'SESSIONS_PER_USER',
    field_class=fields.IntegerField,
    min_value=-1,
    label=_('Maximum number of simultaneous logged in sessions'),
    help_text=_('Maximum number of simultaneous logged in sessions a user may have. To disable enter -1.'),
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
register(
    'OAUTH2_PROVIDER',
    field_class=OAuth2ProviderField,
    default={'ACCESS_TOKEN_EXPIRE_SECONDS': 315360000000,
             'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600},
    label=_('OAuth 2 Timeout Settings'),
    help_text=_('Dictionary for customizing OAuth 2 timeouts, available items are '
                '`ACCESS_TOKEN_EXPIRE_SECONDS`, the duration of access tokens in the number '
                'of seconds, and `AUTHORIZATION_CODE_EXPIRE_SECONDS`, the duration of '
                'authorization grants in the number of seconds.'),
    category=_('Authentication'),
    category_slug='authentication',
)
