# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand

from awx.main.models import Instance, ReceptorAddress


def add_address(**kwargs):
    try:
        instance = Instance.objects.get(hostname=kwargs.pop('instance'))
        kwargs['instance'] = instance

        if kwargs.get('canonical') and instance.receptor_addresses.filter(canonical=True).exclude(address=kwargs['address']).exists():
            print(f"Instance {instance.hostname} already has a canonical address, skipping")
            return False
        # if ReceptorAddress already exists with address, just update
        # otherwise, create new ReceptorAddress
        addr, _ = ReceptorAddress.objects.update_or_create(address=kwargs.pop('address'), defaults=kwargs)
        print(f"Successfully added receptor address {addr.get_full_address()}")
        return True
    except Exception as e:
        print(f"Error adding receptor address: {e}")
        return False


class Command(BaseCommand):
    """
    Internal controller command.
    Register receptor address to an already-registered instance.
    """

    help = "Add receptor address to an instance."

    def add_arguments(self, parser):
        parser.add_argument('--instance', dest='instance', required=True, type=str, help="Instance hostname this address is added to")
        parser.add_argument('--address', dest='address', required=True, type=str, help="Receptor address")
        parser.add_argument('--port', dest='port', type=int, help="Receptor listener port")
        parser.add_argument('--websocket_path', dest='websocket_path', type=str, default="", help="Path for websockets")
        parser.add_argument('--is_internal', action='store_true', help="If true, address only resolvable within the Kubernetes cluster")
        parser.add_argument('--protocol', type=str, default='tcp', choices=['tcp', 'ws', 'wss'], help="Protocol to use for the Receptor listener")
        parser.add_argument('--canonical', action='store_true', help="If true, address is the canonical address for the instance")
        parser.add_argument('--peers_from_control_nodes', action='store_true', help="If true, control nodes will peer to this address")

    def handle(self, **options):
        address_options = {
            k: options[k]
            for k in ('instance', 'address', 'port', 'websocket_path', 'is_internal', 'protocol', 'peers_from_control_nodes', 'canonical')
            if options[k]
        }
        changed = add_address(**address_options)
        if changed:
            print("(changed: True)")
