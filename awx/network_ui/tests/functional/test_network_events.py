import mock
import json
import logging

from awx.network_ui.consumers import networking_events_dispatcher
from awx.network_ui.models import Topology, Device, Link, Interface


def message(message):
    def wrapper(fn):
        fn.tests_message = message
        return fn
    return wrapper


@message('DeviceMove')
def test_network_events_handle_message_DeviceMove():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['DeviceMove', dict(
        msg_type='DeviceMove',
        sender=1,
        id=1,
        x=100,
        y=100,
        previous_x=0,
        previous_y=0
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects') as device_objects_mock:
        networking_events_dispatcher.handle(message)
        device_objects_mock.filter.assert_called_once_with(
            cid=1, topology_id=1)
        device_objects_mock.filter.return_value.update.assert_called_once_with(
            x=100, y=100)
        log_mock.assert_not_called()


@message('DeviceCreate')
def test_network_events_handle_message_DeviceCreate():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['DeviceCreate', dict(msg_type='DeviceCreate',
                                         sender=1,
                                         id=1,
                                         x=0,
                                         y=0,
                                         name="test_created",
                                         type='host',
                                         host_id=None)]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}

    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Topology.objects, 'filter') as topology_objects_mock,\
            mock.patch.object(Device.objects, 'get_or_create') as device_objects_mock:
        device_mock = mock.MagicMock()
        filter_mock = mock.MagicMock()
        device_objects_mock.return_value = [device_mock, True]
        topology_objects_mock.return_value = filter_mock
        networking_events_dispatcher.handle(message)
        device_objects_mock.assert_called_once_with(
            cid=1,
            defaults={'name': u'test_created', 'cid': 1, 'device_type': u'host',
                      'x': 0, 'y': 0, 'host_id': None},
            topology_id=1)
        device_mock.save.assert_called_once_with()
        topology_objects_mock.assert_called_once_with(
            device_id_seq__lt=1, pk=1)
        filter_mock.update.assert_called_once_with(device_id_seq=1)
        log_mock.assert_not_called()


@message('DeviceLabelEdit')
def test_network_events_handle_message_DeviceLabelEdit():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['DeviceLabelEdit', dict(
        msg_type='DeviceLabelEdit',
        sender=1,
        id=1,
        name='test_changed',
        previous_name='test_created'
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device.objects, 'filter') as device_objects_filter_mock:
        networking_events_dispatcher.handle(message)
        device_objects_filter_mock.assert_called_once_with(
            cid=1, topology_id=1)
        log_mock.assert_not_called()


@message('DeviceSelected')
def test_network_events_handle_message_DeviceSelected():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['DeviceSelected', dict(
        msg_type='DeviceSelected',
        sender=1,
        id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle(message)
        log_mock.assert_not_called()


@message('DeviceUnSelected')
def test_network_events_handle_message_DeviceUnSelected():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['DeviceUnSelected', dict(
        msg_type='DeviceUnSelected',
        sender=1,
        id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle(message)
        log_mock.assert_not_called()


@message('DeviceDestroy')
def test_network_events_handle_message_DeviceDestory():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['DeviceDestroy', dict(
        msg_type='DeviceDestroy',
        sender=1,
        id=1,
        previous_x=0,
        previous_y=0,
        previous_name="",
        previous_type="host",
        previous_host_id="1")]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects') as device_objects_mock:
        networking_events_dispatcher.handle(message)
        device_objects_mock.filter.assert_called_once_with(
            cid=1, topology_id=1)
        device_objects_mock.filter.return_value.delete.assert_called_once_with()
        log_mock.assert_not_called()


@message('InterfaceCreate')
def test_network_events_handle_message_InterfaceCreate():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['InterfaceCreate', dict(
        msg_type='InterfaceCreate',
        sender=1,
        device_id=1,
        id=1,
        name='eth0'
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects') as device_objects_mock,\
            mock.patch.object(Interface, 'objects') as interface_objects_mock:
        device_objects_mock.get.return_value.pk = 99
        networking_events_dispatcher.handle(message)
        device_objects_mock.get.assert_called_once_with(cid=1, topology_id=1)
        device_objects_mock.filter.assert_called_once_with(
            cid=1, interface_id_seq__lt=1, topology_id=1)
        interface_objects_mock.get_or_create.assert_called_once_with(
            cid=1, defaults={'name': u'eth0'}, device_id=99)
        log_mock.assert_not_called()


@message('InterfaceLabelEdit')
def test_network_events_handle_message_InterfaceLabelEdit():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['InterfaceLabelEdit', dict(
        msg_type='InterfaceLabelEdit',
        sender=1,
        id=1,
        device_id=1,
        name='new name',
        previous_name='old name'
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Interface, 'objects') as interface_objects_mock:
        networking_events_dispatcher.handle(message)
        interface_objects_mock.filter.assert_called_once_with(
            cid=1, device__cid=1, device__topology_id=1)
        interface_objects_mock.filter.return_value.update.assert_called_once_with(
            name=u'new name')
        log_mock.assert_not_called()


@message('LinkLabelEdit')
def test_network_events_handle_message_LinkLabelEdit():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkLabelEdit', dict(
        msg_type='LinkLabelEdit',
        sender=1,
        id=1,
        name='new name',
        previous_name='old name'
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Link, 'objects') as link_objects_mock:
        networking_events_dispatcher.handle(message)
        link_objects_mock.filter.assert_called_once_with(
            cid=1, from_device__topology_id=1)
        link_objects_mock.filter.return_value.update.assert_called_once_with(
            name=u'new name')
        log_mock.assert_not_called()


@message('LinkCreate')
def test_network_events_handle_message_LinkCreate():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkCreate', dict(
        msg_type='LinkCreate',
        id=1,
        sender=1,
        name="",
        from_device_id=1,
        to_device_id=2,
        from_interface_id=1,
        to_interface_id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects') as device_objects_mock,\
            mock.patch.object(Link, 'objects') as link_objects_mock,\
            mock.patch.object(Interface, 'objects') as interface_objects_mock,\
            mock.patch.object(Topology, 'objects') as topology_objects_mock:
        values_list_mock = mock.MagicMock()
        values_list_mock.values_list.return_value = [(1,1), (2,2)]
        interface_objects_mock.get.return_value = mock.MagicMock()
        interface_objects_mock.get.return_value.pk = 7
        device_objects_mock.filter.return_value = values_list_mock
        topology_objects_mock.filter.return_value = mock.MagicMock()
        networking_events_dispatcher.handle(message)
        device_objects_mock.filter.assert_called_once_with(
            cid__in=[1, 2], topology_id=1)
        values_list_mock.values_list.assert_called_once_with('cid', 'pk')
        link_objects_mock.get_or_create.assert_called_once_with(
            cid=1, from_device_id=1, from_interface_id=7, name=u'',
            to_device_id=2, to_interface_id=7)
        topology_objects_mock.filter.assert_called_once_with(
            link_id_seq__lt=1, pk=1)
        topology_objects_mock.filter.return_value.update.assert_called_once_with(
            link_id_seq=1)
        log_mock.assert_not_called()


@message('LinkCreate')
def test_network_events_handle_message_LinkCreate_bad_device1():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkCreate', dict(
        msg_type='LinkCreate',
        id=1,
        sender=1,
        name="",
        from_device_id=1,
        to_device_id=2,
        from_interface_id=1,
        to_interface_id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects') as device_objects_mock,\
            mock.patch.object(Link, 'objects'),\
            mock.patch.object(Interface, 'objects') as interface_objects_mock,\
            mock.patch.object(Topology, 'objects') as topology_objects_mock:
        values_list_mock = mock.MagicMock()
        values_list_mock.values_list.return_value = [(9,1), (2,2)]
        interface_objects_mock.get.return_value = mock.MagicMock()
        interface_objects_mock.get.return_value.pk = 7
        device_objects_mock.filter.return_value = values_list_mock
        topology_objects_mock.filter.return_value = mock.MagicMock()
        networking_events_dispatcher.handle(message)
        device_objects_mock.filter.assert_called_once_with(
            cid__in=[1, 2], topology_id=1)
        values_list_mock.values_list.assert_called_once_with('cid', 'pk')
        log_mock.assert_called_once_with('Device not found')


@message('LinkCreate')
def test_network_events_handle_message_LinkCreate_bad_device2():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkCreate', dict(
        msg_type='LinkCreate',
        id=1,
        sender=1,
        name="",
        from_device_id=1,
        to_device_id=2,
        from_interface_id=1,
        to_interface_id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects') as device_objects_mock,\
            mock.patch.object(Link, 'objects'),\
            mock.patch.object(Interface, 'objects') as interface_objects_mock,\
            mock.patch.object(Topology, 'objects') as topology_objects_mock:
        values_list_mock = mock.MagicMock()
        values_list_mock.values_list.return_value = [(1,1), (9,2)]
        interface_objects_mock.get.return_value = mock.MagicMock()
        interface_objects_mock.get.return_value.pk = 7
        device_objects_mock.filter.return_value = values_list_mock
        topology_objects_mock.filter.return_value = mock.MagicMock()
        networking_events_dispatcher.handle(message)
        device_objects_mock.filter.assert_called_once_with(
            cid__in=[1, 2], topology_id=1)
        values_list_mock.values_list.assert_called_once_with('cid', 'pk')
        log_mock.assert_called_once_with('Device not found')


@message('LinkDestroy')
def test_network_events_handle_message_LinkDestroy():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkDestroy', dict(
        msg_type='LinkDestroy',
        id=1,
        sender=1,
        name="",
        from_device_id=1,
        to_device_id=2,
        from_interface_id=1,
        to_interface_id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device.objects, 'filter') as device_filter_mock,\
            mock.patch.object(Link.objects, 'filter') as link_filter_mock,\
            mock.patch.object(Interface.objects, 'get') as interface_get_mock:
        values_mock = mock.MagicMock()
        interface_get_mock.return_value = mock.MagicMock()
        interface_get_mock.return_value.pk = 7
        device_filter_mock.return_value = values_mock
        values_mock.values_list.return_value = [(1,1), (2,2)]
        networking_events_dispatcher.handle(message)
        device_filter_mock.assert_called_once_with(
            cid__in=[1, 2], topology_id=1)
        values_mock.values_list.assert_called_once_with('cid', 'pk')
        link_filter_mock.assert_called_once_with(
            cid=1, from_device_id=1, from_interface_id=7, to_device_id=2, to_interface_id=7)
        log_mock.assert_not_called()


@message('LinkDestroy')
def test_network_events_handle_message_LinkDestroy_bad_device_map1():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkDestroy', dict(
        msg_type='LinkDestroy',
        id=1,
        sender=1,
        name="",
        from_device_id=1,
        to_device_id=2,
        from_interface_id=1,
        to_interface_id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device.objects, 'filter') as device_filter_mock,\
            mock.patch.object(Link.objects, 'filter'),\
            mock.patch.object(Interface.objects, 'get') as interface_get_mock:
        values_mock = mock.MagicMock()
        interface_get_mock.return_value = mock.MagicMock()
        interface_get_mock.return_value.pk = 7
        device_filter_mock.return_value = values_mock
        values_mock.values_list.return_value = [(9,1), (2,2)]
        networking_events_dispatcher.handle(message)
        log_mock.assert_called_once_with('Device not found')


@message('LinkDestroy')
def test_network_events_handle_message_LinkDestroy_bad_device_map2():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkDestroy', dict(
        msg_type='LinkDestroy',
        id=1,
        sender=1,
        name="",
        from_device_id=1,
        to_device_id=2,
        from_interface_id=1,
        to_interface_id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device.objects, 'filter') as device_filter_mock,\
            mock.patch.object(Link.objects, 'filter'),\
            mock.patch.object(Interface.objects, 'get') as interface_get_mock:
        values_mock = mock.MagicMock()
        interface_get_mock.return_value = mock.MagicMock()
        interface_get_mock.return_value.pk = 7
        device_filter_mock.return_value = values_mock
        values_mock.values_list.return_value = [(1,1), (9,2)]
        networking_events_dispatcher.handle(message)
        log_mock.assert_called_once_with('Device not found')


@message('LinkSelected')
def test_network_events_handle_message_LinkSelected():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkSelected', dict(
        msg_type='LinkSelected',
        sender=1,
        id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle(message)
        log_mock.assert_not_called()


@message('LinkUnSelected')
def test_network_events_handle_message_LinkUnSelected():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['LinkUnSelected', dict(
        msg_type='LinkUnSelected',
        sender=1,
        id=1
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle(message)
        log_mock.assert_not_called()


@message('MultipleMessage')
def test_network_events_handle_message_MultipleMessage_unsupported_message():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['MultipleMessage', dict(
        msg_type='MultipleMessage',
        sender=1,
        messages=[dict(msg_type="Unsupported")]
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle(message)
        log_mock.assert_called_once_with(
            'Unsupported message %s', u'Unsupported')


@message('MultipleMessage')
def test_network_events_handle_message_MultipleMessage():
    logger = logging.getLogger('awx.network_ui.consumers')
    message_data = ['MultipleMessage', dict(
        msg_type='MultipleMessage',
        sender=1,
        messages=[dict(msg_type="DeviceSelected")]
    )]
    message = {'topology': 1, 'client': 1, 'text': json.dumps(message_data)}
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle(message)
        log_mock.assert_not_called()
