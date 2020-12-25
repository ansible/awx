# Django
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.conf import fields, register
from awx.api.fields import OAuth2ProviderField
from oauth2_provider.settings import oauth2_settings


register(
    'SESSION_COOKIE_AGE',
    field_class=fields.IntegerField,
    min_value=60,
    max_value=30000000000,  # approx 1,000 years, higher values give OverflowError
    label=_('Idle Time Force Log Out'),
    help_text=_('Number of seconds that a user is inactive before they will need to login again.'),
    category=_('Authentication'),
    category_slug='authentication',
    unit=_('seconds'),
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
    default={'ACCESS_TOKEN_EXPIRE_SECONDS': oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS,
             'AUTHORIZATION_CODE_EXPIRE_SECONDS': oauth2_settings.AUTHORIZATION_CODE_EXPIRE_SECONDS,
             'REFRESH_TOKEN_EXPIRE_SECONDS': oauth2_settings.REFRESH_TOKEN_EXPIRE_SECONDS},
    label=_('OAuth 2 Timeout Settings'),
    help_text=_('Dictionary for customizing OAuth 2 timeouts, available items are '
                '`ACCESS_TOKEN_EXPIRE_SECONDS`, the duration of access tokens in the number '
                'of seconds, `AUTHORIZATION_CODE_EXPIRE_SECONDS`, the duration of '
                'authorization codes in the number of seconds, and `REFRESH_TOKEN_EXPIRE_SECONDS`, '
                'the duration of refresh tokens, after expired access tokens, '
                'in the number of seconds.'),
    category=_('Authentication'),
    category_slug='authentication',
    unit=_('seconds'),
)
register(
    'ALLOW_OAUTH2_FOR_EXTERNAL_USERS',
    field_class=fields.BooleanField,
    default=False,
    label=_('Allow External Users to Create OAuth2 Tokens'),
    help_text=_('For security reasons, users from external auth providers (LDAP, SAML, '
                'SSO, Radius, and others) are not allowed to create OAuth2 tokens. '
                'To change this behavior, enable this setting. Existing tokens will '
                'not be deleted when this setting is toggled off.'),
    category=_('Authentication'),
    category_slug='authentication',
)
register(
    'LOGIN_REDIRECT_OVERRIDE',
    field_class=fields.CharField,
    allow_blank=True,
    required=False,
    default='',
    label=_('Login redirect override URL'),
    help_text=_('URL to which unauthorized users will be redirected to log in. '
                'If blank, users will be sent to the Tower login page.'),
    category=_('Authentication'),
    category_slug='authentication',
)
