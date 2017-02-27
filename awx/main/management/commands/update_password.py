# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved

# Python
from optparse import make_option

# Django
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.contrib.auth.models import User


class UpdatePassword(object):
    def update_password(self, username, password):
        changed = False
        u = User.objects.get(username=username)
        if not u:
            raise RuntimeError("User not found")
        check = u.check_password(password)
        if not check:
            u.set_password(password)
            u.save()
            changed = True
        return changed


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--username', dest='username', action='store', type='string', default=None,
                    help='username to change the password for'),
        make_option('--password', dest='password', action='store', type='string', default=None,
                    help='new password for user'),
    )

    def handle(self, *args, **options):
        if not options['username']:
            raise CommandError('username required')
        if not options['password']:
            raise CommandError('password required')

        cp = UpdatePassword()
        res = cp.update_password(options['username'], options['password'])
        if res:
            return "Password updated"
        return "Password not updated"


