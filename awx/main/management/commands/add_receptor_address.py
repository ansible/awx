# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import os

from django.core.management.base import BaseCommand
from django.db import transaction

from awx.main.models import Instance, ReceptorAddress


class Command(BaseCommand):
    """
    Internal tower command.
    Register receptor address to an already-registered instance.
    """

    help = "Add receptor address to an instance."

    def add_arguments(self, parser):
        parser.add_argument('--hostname', dest='hostname', type=str, help="Hostname this address is added to")
        parser.add_argument('--address', dest='address', type=str, help="Receptor address")
        parser.add_argument('--port', dest='port', type=int, help="Receptor listener port")
        parser.add_argument('--protocol', dest='protocol', type=str, default='tcp', choices=['tcp', 'ws'], help="Protocol of the backend connection")
        parser.add_argument('--websocket_path', dest='websocket_path', type=str, default="", help="Path for websockets")
        parser.add_argument(
            '--is_internal', dest='is_internal', type=bool, default=False, help="If true, address only resolvable within the Kubernetes cluster"
        )

    def _add_address(self, **kwargs):
        i = Instance.objects.get(hostname=kwargs.pop('hostname'))
        kwargs['instance'] = i
        ReceptorAddress.objects.create(**kwargs)

    @transaction.atomic
    def handle(self, **options):
        address_options = {k: options[k] for k in ('hostname', 'address', 'port', 'protocol', 'websocket_path', 'is_internal')}
        self._add_address(**address_options)
