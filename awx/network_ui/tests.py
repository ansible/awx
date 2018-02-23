# Copyright (c) 2017 Red Hat, Inc
from django.test import TestCase

# Create your tests here.

from awx.network_ui.models import Topology, Device, Interface, MessageType, Link


class TestToString(TestCase):

    def test(self):
        print str(Topology(name='foo'))
        print str(Device(name='foo'))
        print str(Device(name='foo'))
        print str(Interface(name='foo'))
        print str(MessageType(name='foo'))
        print str(Link(name='foo'))
