from django.core.management.base import BaseCommand
from network_ui.models import Topology, Device, Link

import math



class Command(BaseCommand):
    help = 'Creates a fully connected topology with n nodes'

    def add_arguments(self, parser):
        parser.add_argument('n', type=int)

    def handle(self, *args, **options):

        n = options['n']

        topology = Topology(name="test_{0}".format(n), scale=1.0, panX=0, panY=0)
        topology.save()

        devices = []

        r = 1000
        if n > 0:
            arc_radians = 2 * math.pi / n
        else:
            arc_radians = 2 * math.pi


        for i in xrange(n):
            device = Device(name="R{0}".format(i),
                            x=math.cos(arc_radians*i)*r,
                            y=math.sin(arc_radians*i)*r,
                            id=i,
                            type="router",
                            topology_id=topology.pk)
            devices.append(device)

        Device.objects.bulk_create(devices)

        devices = {x.id: x for x in Device.objects.filter(topology_id=topology.pk)}

        links = []

        for i in xrange(n):
            for j in xrange(i):
                if i == j:
                    continue
                link = Link(from_device=devices[i],
                            to_device=devices[j])
                links.append(link)
        Link.objects.bulk_create(links)

        print "Topology: ", topology.pk
