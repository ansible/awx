# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

import sys

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """A command that reports whether a username exists within the
    system or not.
    """
    def handle(self, *args, **options):
        any_not_found = False

        for username in args:
            if User.objects.filter(username=username).count():
                print('User %s exists.' % username)
            else:
                print('User %s does not exist.' % username)
                any_not_found = True
