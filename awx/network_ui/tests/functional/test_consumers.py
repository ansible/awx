
import mock
import logging
import json
import imp
from mock import patch
patch('channels.auth.channel_session_user', lambda x: x).start()
patch('channels.auth.channel_session_user_from_http', lambda x: x).start()

from awx.network_ui.consumers import parse_inventory_id, networking_events_dispatcher, send_snapshot # noqa
from awx.network_ui.models import Topology, Device, Link, Interface, TopologyInventory, Client # noqa
import awx # noqa
import awx.network_ui # noqa
import awx.network_ui.consumers # noqa
imp.reload(awx.network_ui.consumers)


def test_parse_inventory_id():
    assert parse_inventory_id({}) is None
    assert parse_inventory_id({'inventory_id': ['1']}) == 1
    assert parse_inventory_id({'inventory_id': ['0']}) is None
    assert parse_inventory_id({'inventory_id': ['X']}) is None
    assert parse_inventory_id({'inventory_id': []}) is None
    assert parse_inventory_id({'inventory_id': 'x'}) is None
    assert parse_inventory_id({'inventory_id': '12345'}) == 1
    assert parse_inventory_id({'inventory_id': 1}) is None


def test_network_events_handle_message_incomplete_message1():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle({})
        log_mock.assert_called_once_with(
            'Unsupported message %s: no topology', {})


def test_network_events_handle_message_incomplete_message2():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle({'topology': [0]})
        log_mock.assert_called_once_with(
            'Unsupported message %s: no client', {'topology': [0]})


def test_network_events_handle_message_incomplete_message3():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle({'topology': [1]})
        log_mock.assert_called_once_with(
            'Unsupported message %s: no client', {'topology': [1]})


def test_network_events_handle_message_incomplete_message4():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        networking_events_dispatcher.handle({'topology': 1, 'client': 1})
        log_mock.assert_called_once_with('Unsupported message %s: no data', {
                                         'client': 1, 'topology': 1})


def test_network_events_handle_message_incomplete_message5():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        message = ['DeviceCreate']
        networking_events_dispatcher.handle(
            {'topology': 1, 'client': 1, 'text': json.dumps(message)})
        log_mock.assert_called_once_with('Unsupported message %s: no message type', {
                                         'text': '["DeviceCreate"]', 'client': 1, 'topology': 1})


def test_network_events_handle_message_incomplete_message6():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        message = ['DeviceCreate', []]
        networking_events_dispatcher.handle(
            {'topology': 1, 'client': 1, 'text': json.dumps(message)})
        log_mock.assert_has_calls([
            mock.call('Message has no sender'),
            mock.call('Unsupported message %s: no message type', {'text': '["DeviceCreate", []]', 'client': 1, 'topology': 1})])


def test_network_events_handle_message_incomplete_message7():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        message = ['DeviceCreate', {}]
        networking_events_dispatcher.handle(
            {'topology': 1, 'client': 1, 'text': json.dumps(message)})
        log_mock.assert_has_calls([
            mock.call('client_id mismatch expected: %s actual %s', 1, None),
            mock.call('Unsupported message %s: no message type', {'text': '["DeviceCreate", {}]', 'client': 1, 'topology': 1})])


def test_network_events_handle_message_incomplete_message8():
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock:
        message = ['Unsupported', {'sender': 1}]
        networking_events_dispatcher.handle(
            {'topology': 1, 'client': 1, 'text': json.dumps(message)})
        log_mock.assert_called_once_with(
            'Unsupported message %s: no handler', u'Unsupported')


def test_send_snapshot_empty():
    channel = mock.MagicMock()
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects'),\
            mock.patch.object(Link, 'objects'),\
            mock.patch.object(Interface, 'objects'),\
            mock.patch.object(Topology, 'objects'):
        send_snapshot(channel, 1)
        log_mock.assert_not_called()
    channel.send.assert_called_once_with(
        {'text': '["Snapshot", {"links": [], "devices": [], "sender": 0}]'})


def test_send_snapshot_single():
    channel = mock.MagicMock()
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'warning') as log_mock,\
            mock.patch.object(Device, 'objects') as device_objects_mock,\
            mock.patch.object(Link, 'objects'),\
            mock.patch.object(Interface, 'objects') as interface_objects_mock:

        interface_objects_mock.filter.return_value.values.return_value = [
            dict(cid=1, device_id=1, id=1, name="eth0")]
        device_objects_mock.filter.return_value.values.return_value = [
            dict(cid=1, id=1, device_type="host", name="host1", x=0, y=0,
                 interface_id_seq=1, host_id=1)]
        send_snapshot(channel, 1)
        device_objects_mock.filter.assert_called_once_with(topology_id=1)
        device_objects_mock.filter.return_value.values.assert_called_once_with()
        interface_objects_mock.filter.assert_called_once_with(
            device__topology_id=1)
        interface_objects_mock.filter.return_value.values.assert_called_once_with()
        log_mock.assert_not_called()
        channel.send.assert_called_once_with(
            {'text': '''["Snapshot", {"links": [], "devices": [{"interface_id_seq": 1, \
"name": "host1", "interfaces": [{"id": 1, "device_id": 1, "name": "eth0", "interface_id": 1}], \
"device_type": "host", "host_id": 1, "y": 0, "x": 0, "id": 1, "device_id": 1}], "sender": 0}]'''})


def test_ws_disconnect():
    message = mock.MagicMock()
    message.channel_session = dict(topology_id=1)
    message.reply_channel = 'foo'
    with mock.patch('channels.Group') as group_mock:
        awx.network_ui.consumers.ws_disconnect(message)
        group_mock.assert_called_once_with('topology-1')
        group_mock.return_value.discard.assert_called_once_with('foo')


def test_ws_disconnect_no_topology():
    message = mock.MagicMock()
    with mock.patch('channels.Group') as group_mock:
        awx.network_ui.consumers.ws_disconnect(message)
        group_mock.assert_not_called()


def test_ws_message():
    message = mock.MagicMock()
    message.channel_session = dict(topology_id=1, client_id=1)
    message.__getitem__.return_value = json.dumps([])
    print (message['text'])
    with mock.patch('channels.Group') as group_mock:
        awx.network_ui.consumers.ws_message(message)
        group_mock.assert_called_once_with('topology-1')
        group_mock.return_value.send.assert_called_once_with({'text': '[]'})


def test_ws_connect_unauthenticated():
    message = mock.MagicMock()
    message.user.is_authenticated.return_value = False
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch.object(logger, 'error') as log_mock:
        awx.network_ui.consumers.ws_connect(message)
        log_mock.assert_called_once_with('Request user is not authenticated to use websocket.')


def test_ws_connect_new_topology():
    message = mock.MagicMock()
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch('awx.network_ui.consumers.Client') as client_mock,\
            mock.patch('awx.network_ui.consumers.Topology') as topology_mock,\
            mock.patch('channels.Group'),\
            mock.patch('awx.network_ui.consumers.send_snapshot') as send_snapshot_mock,\
            mock.patch.object(logger, 'warning'),\
            mock.patch.object(TopologyInventory, 'objects'),\
            mock.patch.object(TopologyInventory, 'save'),\
            mock.patch.object(Topology, 'save'),\
            mock.patch.object(Topology, 'objects'),\
            mock.patch.object(Device, 'objects'),\
            mock.patch.object(Link, 'objects'),\
            mock.patch.object(Interface, 'objects'):
        client_mock.return_value.pk = 777
        topology_mock.return_value = Topology(
            name="topology", scale=1.0, panX=0, panY=0, pk=999)
        awx.network_ui.consumers.ws_connect(message)
        message.reply_channel.send.assert_has_calls([
            mock.call({'text': '["id", 777]'}),
            mock.call({'text': '["topology_id", 999]'}),
            mock.call(
                {'text': '["Topology", {"scale": 1.0, "name": "topology", "device_id_seq": 0, "panY": 0, "panX": 0, "topology_id": 999, "link_id_seq": 0}]'}),
        ])
        send_snapshot_mock.assert_called_once_with(message.reply_channel, 999)


def test_ws_connect_existing_topology():
    message = mock.MagicMock()
    logger = logging.getLogger('awx.network_ui.consumers')
    with mock.patch('awx.network_ui.consumers.Client') as client_mock,\
            mock.patch('awx.network_ui.consumers.send_snapshot') as send_snapshot_mock,\
            mock.patch('channels.Group'),\
            mock.patch.object(logger, 'warning'),\
            mock.patch.object(TopologyInventory, 'objects') as topology_inventory_objects_mock,\
            mock.patch.object(TopologyInventory, 'save'),\
            mock.patch.object(Topology, 'save'),\
            mock.patch.object(Topology, 'objects') as topology_objects_mock,\
            mock.patch.object(Device, 'objects'),\
            mock.patch.object(Link, 'objects'),\
            mock.patch.object(Interface, 'objects'):
        topology_inventory_objects_mock.filter.return_value.values_list.return_value = [
            1]
        client_mock.return_value.pk = 888
        topology_objects_mock.get.return_value = Topology(pk=1001,
                                                          id=1,
                                                          name="topo",
                                                          panX=0,
                                                          panY=0,
                                                          scale=1.0,
                                                          link_id_seq=1,
                                                          device_id_seq=1)
        awx.network_ui.consumers.ws_connect(message)
        message.reply_channel.send.assert_has_calls([
            mock.call({'text': '["id", 888]'}),
            mock.call({'text': '["topology_id", 1001]'}),
            mock.call(
                {'text': '["Topology", {"scale": 1.0, "name": "topo", "device_id_seq": 1, "panY": 0, "panX": 0, "topology_id": 1001, "link_id_seq": 1}]'}),
        ])
        send_snapshot_mock.assert_called_once_with(message.reply_channel, 1001)
