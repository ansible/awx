# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand

from awx.main.models import Instance, ReceptorAddress


def add_address(**kwargs):
    try:
        instance = Instance.objects.get(hostname=kwargs.pop('hostname'))
        kwargs['instance'] = instance
        # address and protocol are unique together for ReceptorAddress
        # If an address has (address, protocol), it will update the rest of the values suppled in defaults dict
        # if no address exists with (address, protocol), then a new address will be created
        # these unique together fields need to be consistent with the unique constraint in the ReceptorAddress model
        addr, _ = ReceptorAddress.objects.update_or_create(address=kwargs.pop('address'), protocol=kwargs.pop('protocol'), defaults=kwargs)
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
        parser.add_argument('--hostname', dest='hostname', type=str, help="Hostname this address is added to")
        parser.add_argument('--address', dest='address', type=str, help="Receptor address")
        parser.add_argument('--port', dest='port', type=int, help="Receptor listener port")
        parser.add_argument('--protocol', dest='protocol', type=str, default='tcp', choices=['tcp', 'ws'], help="Protocol of the backend connection")
        parser.add_argument('--websocket_path', dest='websocket_path', type=str, default="", help="Path for websockets")
        parser.add_argument('--is_internal', action='store_true', help="If true, address only resolvable within the Kubernetes cluster")
        parser.add_argument('--peers_from_control_nodes', action='store_true', help="If true, control nodes will peer to this address")

    def handle(self, **options):
        self.changed = False
        address_options = {k: options[k] for k in ('hostname', 'address', 'port', 'protocol', 'websocket_path', 'is_internal', 'peers_from_control_nodes')}
        self.changed = add_address(**address_options)
        if self.changed:
            print("(changed: True)")
