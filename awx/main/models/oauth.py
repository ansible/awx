# Python
import re

# Django
from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# Django OAuth Toolkit
from oauth2_provider.models import AbstractApplication, AbstractAccessToken


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

