
import mock

from awx.network_ui.views import topology_data, NetworkAnnotatedInterface, json_topology_data, yaml_topology_data
from awx.network_ui.models import Topology, Device, Link, Interface



def test_topology_data():
    with mock.patch.object(Topology, 'objects'),\
            mock.patch.object(Device, 'objects') as device_objects_mock,\
            mock.patch.object(Link, 'objects') as link_objects_mock,\
            mock.patch.object(Interface, 'objects'),\
            mock.patch.object(NetworkAnnotatedInterface, 'filter'):
        device_objects_mock.filter.return_value.order_by.return_value = [
            Device(pk=1), Device(pk=2)]
        link_objects_mock.filter.return_value = [Link(from_device=Device(name='from', cid=1),
                                                      to_device=Device(
                                                          name='to', cid=2),
                                                      from_interface=Interface(
                                                          name="eth0", cid=1),
                                                      to_interface=Interface(
                                                          name="eth0", cid=1),
                                                      name="",
                                                      pk=1
                                                      )]
        data = topology_data(1)
        assert len(data['devices']) == 2
        assert len(data['links']) == 1


def test_json_topology_data():
    request = mock.MagicMock()
    request.GET = dict(topology_id=1)
    with mock.patch('awx.network_ui.views.topology_data') as topology_data_mock:
        topology_data_mock.return_value = dict()
        json_topology_data(request)
        topology_data_mock.assert_called_once_with(1)


def test_yaml_topology_data():
    request = mock.MagicMock()
    request.GET = dict(topology_id=1)
    with mock.patch('awx.network_ui.views.topology_data') as topology_data_mock:
        topology_data_mock.return_value = dict()
        yaml_topology_data(request)
        topology_data_mock.assert_called_once_with(1)


def test_json_topology_data_no_topology_id():
    request = mock.MagicMock()
    request.GET = dict()
    with mock.patch('awx.network_ui.views.topology_data') as topology_data_mock:
        topology_data_mock.return_value = dict()
        json_topology_data(request)
        topology_data_mock.assert_not_called()


def test_yaml_topology_data_no_topology_id():
    request = mock.MagicMock()
    request.GET = dict()
    with mock.patch('awx.network_ui.views.topology_data') as topology_data_mock:
        topology_data_mock.return_value = dict()
        yaml_topology_data(request)
        topology_data_mock.assert_not_called()
