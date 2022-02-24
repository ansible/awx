# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.commands.migrate import Command as DjangoCommand

from awx.conf.disablement import default_settings


class Command(DjangoCommand):
    def handle(self, *args, **options):
        with default_settings():
            return super().handle(*args, **options)
