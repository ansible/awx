# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python Social Auth
from social.exceptions import AuthException


class AuthInactive(AuthException):
    """Authentication for this user is forbidden"""

    def __str__(self):
        return 'Your account is inactive'


def set_is_active_for_new_user(strategy, details, user=None, *args, **kwargs):
    if kwargs.get('is_new', False):
        details['is_active'] = True
        return {'details': details}


def prevent_inactive_login(backend, details, user=None, *args, **kwargs):
    if user and not user.is_active:
        raise AuthInactive(backend)
