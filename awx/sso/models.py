# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class UserEnterpriseAuth(models.Model):
    """Tower Enterprise Auth association model"""

    PROVIDER_CHOICES = (
        ('radius', _('RADIUS')),
        ('tacacs+', _('TACACS+')),
        ('saml', _('SAML')),
    )

    class Meta:
        unique_together = ('user', 'provider')

    user = models.ForeignKey(
        User, related_name='enterprise_auth', on_delete=models.CASCADE
    )
    provider = models.CharField(
        max_length=32, choices=PROVIDER_CHOICES
    )
