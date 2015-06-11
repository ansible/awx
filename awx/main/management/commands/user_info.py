# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved


from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """A command that reports whether a username exists within the
    system or not.
    """
    def handle(self, *args, **options):
        """Print out information about the user to the console."""

        # Sanity check: There should be one and exactly one positional
        # argument.
        if len(args) != 1:
            raise CommandError('This command requires one positional argument '
                               '(a username).')

        # Get the user.
        try:
            username = args[0]
            user = User.objects.get(username=username)

            # Print a cute header.
            header = 'Information for user: %s' % username
            print('%s\n%s' % (header, '=' * len(header)))

            # Print the email and real name of the user.
            print('Email: %s' % user.email)
            if user.first_name or user.last_name:
                print('Name: %s %s' % (user.first_name, user.last_name))
            else:
                print('No name provided.')
        except User.DoesNotExist:
            raise CommandError('User %s does not exist.' % username)

