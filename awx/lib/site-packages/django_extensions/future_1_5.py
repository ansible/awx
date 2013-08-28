"""
A forwards compatibility module.

Implements some features of Django 1.5 related to the 'Custom User Model' feature
when the application is run with a lower version of Django.
"""
from __future__ import unicode_literals

from django.contrib.auth.models import User

User.USERNAME_FIELD = "username"
User.get_username = lambda self: self.username


def get_user_model():
    return User
