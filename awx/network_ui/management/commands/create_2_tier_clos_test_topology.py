# Copyright (c) 2017 Red Hat, Inc
from django.core.management.base import BaseCommand
from awx.network_ui.models import Topology, Device, Link, Interface

from collections import defaultdict
from .util import natural_numbers


class Command(BaseCommand):
    help = '''Adds a 2 tier clos topology with n nodes in the 1st tier and m nodes
            in the 2nd tier and h hosts per pair of switches to the topology with id `id`'''

    def add_arguments(self, parser):
        parser.add_argument('id', type=int)
        parser.add_argument('n', type=int)
        parser.add_argument('m', type=int)
        parser.add_argument('h', type=int)

    def handle(self, *args, **options):

        topology_id = options['id']
        n = options['n']
        m = options['m']
        h = options['h']

        print "n", n
        print "m", m

        topology = Topology.objects.get(pk=topology_id)

        devices = []
        hosts_per_leaf = []
        leaves = []
        spines = []

        id_seq = natural_numbers(topology.device_id_seq)
        link_id_seq = natural_numbers(topology.link_id_seq)

        tier2 = 100
        tier1 = 500
        tier0 = 900
        spacing = 200

        tier2_centering = ((n - m) * 200) / 2

        for i in xrange(n):
            device = Device(name="Leaf{0}".format(i),
                            x=i * spacing,
                            y=tier1,
                            id=next(id_seq),
                            type="switch",
                            topology_id=topology.pk)
            devices.append(device)
            leaves.append(device)

        for i in xrange(m):
            device = Device(name="Spine{0}".format(i),
                            x=(i * spacing) + tier2_centering,
                            y=tier2,
                            id=next(id_seq),
                            type="switch",
                            topology_id=topology.pk)
            devices.append(device)
            spines.append(device)

        for i in xrange(n / 2):
            hosts = []
            for j in xrange(h):
                device = Device(name="Host{0}-{1}".format(i, j),
                                x=(i * 2 * spacing) + spacing / 2,
                                y=tier0 + (j * 40),
                                id=next(id_seq),
                                type="host",
                                topology_id=topology.pk)
                devices.append(device)
                hosts.append(device)
            hosts_per_leaf.append(hosts)

        print "leaves", leaves
        print "spines", spines
        print "hosts_per_leaf", hosts_per_leaf

        Device.objects.bulk_create(devices)

        devices = {x.id: x for x in Device.objects.filter(topology_id=topology.pk)}

        links = []
        interfaces = defaultdict(list)

        for leaf in leaves:
            for spine in spines:
                from_interface = Interface(device=devices[leaf.id],
                                           name="swp" + str(len(interfaces[leaf.id]) + 1),
                                           id=(len(interfaces[leaf.id]) + 1))
                from_interface.save()
                interfaces[leaf.id].append(from_interface)
                to_interface = Interface(device=devices[spine.id],
                                         name="swp" + str(len(interfaces[spine.id]) + 1),
                                         id=(len(interfaces[spine.id]) + 1))
                to_interface.save()
                interfaces[spine.id].append(to_interface)
                link = Link(from_device=devices[leaf.id],
                            to_device=devices[spine.id],
                            from_interface=from_interface,
                            to_interface=to_interface,
                            id=next(link_id_seq))
                links.append(link)
        for i, hosts in enumerate(hosts_per_leaf):
            leaf1 = leaves[2 * i]
            leaf2 = leaves[2 * i + 1]
            for j, host in enumerate(hosts):
                from_interface = Interface(device=devices[leaf1.id],
                                           name="swp" + str(len(interfaces[leaf1.id]) + 1),
                                           id=(len(interfaces[leaf1.id]) + 1))
                from_interface.save()
                interfaces[leaf1.id].append(from_interface)
                to_interface = Interface(device=devices[host.id],
                                         name="eth" + str(len(interfaces[host.id]) + 1),
                                         id=(len(interfaces[host.id]) + 1))
                to_interface.save()
                interfaces[host.id].append(to_interface)
                link = Link(from_device=devices[leaf1.id],
                            to_device=devices[host.id],
                            from_interface=from_interface,
                            to_interface=to_interface,
                            id=next(link_id_seq))
                links.append(link)
                from_interface = Interface(device=devices[leaf2.id],
                                           name="swp" + str(len(interfaces[leaf2.id]) + 1),
                                           id=(len(interfaces[leaf2.id]) + 1))
                from_interface.save()
                interfaces[leaf2.id].append(from_interface)
                to_interface = Interface(device=devices[host.id],
                                         name="eth" + str(len(interfaces[host.id]) + 1),
                                         id=(len(interfaces[host.id]) + 1))
                to_interface.save()
                interfaces[host.id].append(to_interface)
                link = Link(from_device=devices[leaf2.id],
                            to_device=devices[host.id],
                            from_interface=from_interface,
                            to_interface=to_interface,
                            id=next(link_id_seq))
                links.append(link)

        Link.objects.bulk_create(links)

        topology.device_id_seq = next(id_seq)
        topology.link_id_seq = next(link_id_seq)
        topology.save()

        print "Topology: ", topology.pk
