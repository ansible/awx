# Copyright (c) 2014 Ansible, Inc.
# All Rights Reserved

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from awx.main.models import Instance


class Command(BaseCommand):
    """List instances from the Tower database
    """

    def handle(self, **options):
        for instance in Instance.objects.all():
            print("uuid: %s; hostname: %s; primary: %s; created: %s; modified: %s" %
                  (instance.uuid, instance.hostname, instance.primary, instance.created, instance.modified))
