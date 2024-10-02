# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.contrib.auth.models import User
from django.conf import settings as django_settings

# Ansible Tower
from awx.sso.models import UserEnterpriseAuth

logger = logging.getLogger('awx.sso.backends')


def _decorate_enterprise_user(user, provider):
    user.set_unusable_password()
    user.save()
    enterprise_auth, _ = UserEnterpriseAuth.objects.get_or_create(user=user, provider=provider)
    return enterprise_auth


def _get_or_set_enterprise_user(username, password, provider):
    created = False
    try:
        user = User.objects.prefetch_related('enterprise_auth').get(username=username)
    except User.DoesNotExist:
        user = User(username=username)
        enterprise_auth = _decorate_enterprise_user(user, provider)
        logger.debug("Created enterprise user %s via %s backend." % (username, enterprise_auth.get_provider_display()))
        created = True
    if created or user.is_in_enterprise_category(provider):
        return user
    logger.warning("Enterprise user %s already defined in Tower." % username)
