# Python
import re

# Django
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# Django OAuth Toolkit
from oauth2_provider.models import AbstractApplication, AbstractAccessToken
from oauth2_provider.generators import generate_client_secret

from awx.main.fields import OAuth2ClientSecretField


DATA_URI_RE = re.compile(r'.*')  # FIXME

__all__ = ['OAuth2AccessToken', 'OAuth2Application']


class OAuth2Application(AbstractApplication):

    class Meta:
        app_label = 'main'
        verbose_name = _('application')

    description = models.TextField(
        default='',
        blank=True,
    )
    logo_data = models.TextField(
        default='',
        editable=False,
        validators=[RegexValidator(DATA_URI_RE)],
    )
    organization = models.ForeignKey(
        'Organization',
        related_name='applications',
        help_text=_('Organization containing this application.'),
        on_delete=models.CASCADE,
        null=True,
    )

    client_secret = OAuth2ClientSecretField(
        max_length=1024, blank=True, default=generate_client_secret, db_index=True
    )


class OAuth2AccessToken(AbstractAccessToken):

    class Meta:
        app_label = 'main'
        verbose_name = _('access token')

    description = models.CharField(
        max_length=200,
        default='',
        blank=True,
    )
    last_used = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
    )

    def is_valid(self, scopes=None):
        valid = super(OAuth2AccessToken, self).is_valid(scopes)
        if valid:
            self.last_used = now()
            self.save(update_fields=['last_used'])
        return valid

