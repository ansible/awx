# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


# todo: this model to be removed as part of sso removal issue AAP-28380
class UserEnterpriseAuth(models.Model):
    """Enterprise Auth association model"""

    PROVIDER_CHOICES = (('radius', _('RADIUS')), ('tacacs+', _('TACACS+')))

    class Meta:
        unique_together = ('user', 'provider')

    user = models.ForeignKey(User, related_name='enterprise_auth', on_delete=models.CASCADE)
    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES)
