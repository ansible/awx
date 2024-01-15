# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand

from awx.main.models import Instance, ReceptorAddress


def add_address(**kwargs):
    try:
        instance = Instance.objects.get(hostname=kwargs.pop('instance'))
        kwargs['instance'] = instance
        # if ReceptorAddress already exists with address, just update
        # otherwise, create new ReceptorAddress
        addr, _ = ReceptorAddress.objects.update_or_create(address=kwargs.pop('address'), defaults=kwargs)
        print(f"Successfully added receptor address {addr.get_full_address()}")
        changed = True
    except Exception as e:
        changed = False
        print(f"Error adding receptor address: {e}")
    return changed


class Command(BaseCommand):
    """
    Internal tower command.
    Register receptor address to an already-registered instance.
    """

    help = "Add receptor address to an instance."

    def add_arguments(self, parser):
        parser.add_argument('--instance', dest='instance', type=str, help="Instance hostname this address is added to")
        parser.add_argument('--address', dest='address', type=str, help="Receptor address")
        parser.add_argument('--port', dest='port', type=int, help="Receptor listener port")
        parser.add_argument('--websocket_path', dest='websocket_path', type=str, default="", help="Path for websockets")
        parser.add_argument('--is_internal', action='store_true', help="If true, address only resolvable within the Kubernetes cluster")
        parser.add_argument('--protocol', type=str, default='tcp', choices=['tcp', 'ws', 'wss'], help="Protocol to use for the Receptor listener")
        parser.add_argument('--canonical', action='store_true', help="If true, address is the canonical address for the instance")
        parser.add_argument('--peers_from_control_nodes', action='store_true', help="If true, control nodes will peer to this address")

    def handle(self, **options):
        self.changed = False
        address_options = {
            k: options[k]
            for k in ('instance', 'address', 'port', 'websocket_path', 'is_internal', 'protocol', 'peers_from_control_nodes', 'canonical')
            if options[k]
        }
        self.changed = add_address(**address_options)
        if self.changed:
            print("(changed: True)")
