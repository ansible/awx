# Copyright (c) 2017 Red Hat, Inc
from django.core.management.base import BaseCommand
from awx.network_ui.models import Topology, Device, Link, Interface

import math

from collections import defaultdict
from .util import natural_numbers


class Command(BaseCommand):
    help = 'Adds a fully connected topology with n nodes to topology pk id'

    def add_arguments(self, parser):
        parser.add_argument('id', type=int)
        parser.add_argument('n', type=int)

    def handle(self, *args, **options):

        topology_id = options['id']
        n = options['n']

        topology = Topology.objects.get(topology_id=topology_id)

        link_id_seq = natural_numbers(topology.link_id_seq)
        device_id_seq = natural_numbers(topology.device_id_seq)
        devices = []

        r = 1000
        if n > 0:
            arc_radians = 2 * math.pi / n
        else:
            arc_radians = 2 * math.pi


        for i in xrange(n):
            device = Device(name="R{0}".format(i),
                            x=math.cos(arc_radians * i) * r,
                            y=math.sin(arc_radians * i) * r,
                            id=next(device_id_seq),
                            type="router",
                            topology_id=topology.pk)
            devices.append(device)

        Device.objects.bulk_create(devices)

        devices = list(Device.objects.filter(topology_id=topology.pk))

        links = []
        interfaces = defaultdict(list)

        for i in xrange(n):
            for j in xrange(i):
                if i == j:
                    continue
                from_interface = Interface(device=devices[i],
                                           name="swp" + str(len(interfaces[i]) + 1),
                                           id=(len(interfaces[i]) + 1))
                from_interface.save()
                interfaces[i].append(from_interface)
                to_interface = Interface(device=devices[j],
                                         name="swp" + str(len(interfaces[j]) + 1),
                                         id=(len(interfaces[j]) + 1))
                to_interface.save()
                interfaces[j].append(to_interface)
                link = Link(from_device=devices[i],
                            to_device=devices[j],
                            from_interface=from_interface,
                            to_interface=to_interface,
                            id=next(link_id_seq))
                links.append(link)
        Link.objects.bulk_create(links)

        print "Topology: ", topology.pk
