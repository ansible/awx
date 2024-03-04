# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand

from awx.main.models import ReceptorAddress


class Command(BaseCommand):
    """
    Internal controller command.
    Delete a receptor address.
    """

    help = "Add receptor address to an instance."

    def add_arguments(self, parser):
        parser.add_argument('--address', dest='address', type=str, help="Receptor address to remove")

    def handle(self, **options):
        deleted = ReceptorAddress.objects.filter(address=options['address']).delete()
        if deleted[0]:
            print(f"Successfully removed {options['address']}")
            print("(changed: True)")
        else:
            print(f"Did not remove {options['address']}, not found")
