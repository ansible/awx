

from awx.network_ui.models import Device, Topology, Interface


def test_device():
    assert str(Device(name="foo")) == "foo"


def test_topology():
    assert str(Topology(name="foo")) == "foo"


def test_interface():
    assert str(Interface(name="foo")) == "foo"
