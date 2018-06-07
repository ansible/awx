import pytest

import inspect

from awx.network_ui.models import Device, Topology, Interface, Link

from awx.main.models import Organization, Inventory
from awx.main.tasks import delete_inventory

from django.db.models import Model


def test_device():
    assert str(Device(name="foo")) == "foo"


def test_topology():
    assert str(Topology(name="foo")) == "foo"


def test_interface():
    assert str(Interface(name="foo")) == "foo"


@pytest.mark.django_db
def test_deletion():
    org = Organization.objects.create(name='Default')
    inv = Inventory.objects.create(name='inv', organization=org)
    host1 = inv.hosts.create(name='foo')
    host2 = inv.hosts.create(name='bar')
    topology = Topology.objects.create(
        name='inv', scale=0.7, panX=0.0, panY=0.0
    )
    inv.topologyinventory_set.create(topology=topology)
    device1 = topology.device_set.create(name='foo', host=host1, x=0.0, y=0.0, cid=1)
    interface1 = Interface.objects.create(device=device1, name='foo', cid=2)
    device2 = topology.device_set.create(name='bar', host=host2, x=0.0, y=0.0, cid=3)
    interface2 = Interface.objects.create(device=device2, name='bar', cid=4)
    Link.objects.create(
        from_device=device1, to_device=device2,
        from_interface=interface1, to_interface=interface2,
        cid=10
    )

    network_ui_models = []
    from awx.network_ui import models as network_models
    for name, model in vars(network_models).items():
        if not inspect.isclass(model) or not issubclass(model, Model):
            continue
        network_ui_models.append(model)

    delete_inventory.run(inv.pk, None)
    for cls in network_ui_models:
        assert cls.objects.count() == 0, cls
