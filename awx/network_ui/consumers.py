# Copyright (c) 2017 Red Hat, Inc
# In consumers.py
from channels import Group, Channel
from channels.sessions import channel_session
from awx.network_ui.models import Topology, Device, Link, Client, TopologyHistory, MessageType, Interface
from awx.network_ui.models import Group as DeviceGroup
from awx.network_ui.models import GroupDevice as GroupDeviceMap
from awx.network_ui.models import DataSheet, DataBinding, DataType
from awx.network_ui.models import Process, Stream
from awx.network_ui.models import Toolbox, ToolboxItem
from awx.network_ui.models import FSMTrace, EventTrace, Coverage, TopologySnapshot
from awx.network_ui.models import TopologyInventory
from awx.network_ui.models import TestCase, TestResult, CodeUnderTest, Result
from awx.network_ui.messages import MultipleMessage, InterfaceCreate, LinkCreate, to_dict
import urlparse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from collections import defaultdict
import math
import random
import logging
from django.utils.dateparse import parse_datetime


from awx.network_ui.utils import transform_dict
import dpath.util
from pprint import pformat

import json
# Connected to websocket.connect

HISTORY_MESSAGE_IGNORE_TYPES = ['DeviceSelected',
                                'DeviceUnSelected',
                                'LinkSelected',
                                'LinkUnSelected',
                                'Undo',
                                'Redo',
                                'MouseEvent',
                                'MouseWheelEvent',
                                'KeyEvent']


SPACING = 200
RACK_SPACING = 50

logger = logging.getLogger("awx.network_ui.consumers")


def circular_layout(topology_id):
    n = Device.objects.filter(topology_id=topology_id).count()

    r = 200
    if n > 0:
        arc_radians = 2 * math.pi / n
    else:
        arc_radians = 2 * math.pi

    for i, device in enumerate(Device.objects.filter(topology_id=topology_id)):
        device.x = math.cos(arc_radians * i + math.pi / 4) * r
        device.y = math.sin(arc_radians * i + math.pi / 4) * r
        device.save()

    send_snapshot(Group("topology-%s" % topology_id), topology_id)


def v_distance(graph, grid, device):

    d = 0
    for edge in graph['edges'][device]:
        d += math.sqrt(math.pow(device.x - edge.x, 2) + math.pow(device.y - edge.y, 2))

    return d


def reduce_distance(graph, grid):

    devices = graph['vertices']

    def sum_distances():
        distances = {x: v_distance(graph, grid, x) for x in grid.keys()}
        return sum(distances.values())

    total_distance = sum_distances()

    for i in xrange(10000):
        a = random.choice(devices)
        b = random.choice(devices)
        if a == b:
            continue
        else:
            swap(grid, a, b)
            place(grid, a)
            place(grid, b)
            new_total = sum_distances()
            if new_total < total_distance:
                print "New total", new_total
                total_distance = new_total
                a.save()
                b.save()
            else:
                swap(grid, a, b)
                place(grid, a)
                place(grid, b)


def place(grid, device):
    device.x = grid[device][1] * SPACING
    device.y = grid[device][0] * SPACING


def swap(grid, a, b):
    tmp = grid[a]
    grid[a] = grid[b]
    grid[b] = tmp


def grid_layout(topology_id):
    n = Device.objects.filter(topology_id=topology_id).count()

    cols = rows = int(math.ceil(math.sqrt(n)))

    def device_seq_generator():
        for d in Device.objects.filter(topology_id=topology_id):
            yield d

    device_seq = device_seq_generator()

    grid = {}
    graph = dict(vertices=[], edges=defaultdict(list))

    links = Link.objects.filter(Q(from_device__topology_id=topology_id) |
                                Q(to_device__topology_id=topology_id))

    for l in links:
        graph['edges'][l.from_device].append(l.to_device)
        graph['edges'][l.to_device].append(l.from_device)

    for i in xrange(rows):
        for j in xrange(cols):
            try:
                device = next(device_seq)
                graph['vertices'].append(device)
                grid[device] = (i, j)
                place(grid, device)
                device.save()
            except StopIteration:
                pass

    reduce_distance(graph, grid)

    send_snapshot(Group("topology-%s" % topology_id), topology_id)


def tier_layout(topology_id):

    devices = list(Device.objects.filter(topology_id=topology_id))
    device_map = {x.pk: x for x in devices}
    links = Link.objects.filter(Q(from_device__topology_id=topology_id) |
                                Q(to_device__topology_id=topology_id))

    def guess_role(devices):

        for device in devices:
            if getattr(device, "role", None):
                continue
            if device.type == "host":
                device.role = "host"
                continue
            if device.type == "switch":
                if 'leaf' in device.name.lower():
                    device.role = "leaf"
                    continue
                if 'spine' in device.name.lower():
                    device.role = "spine"
                    continue
            device.role = "unknown"

    guess_role(devices)

    edges = defaultdict(set)
    racks = []

    for l in links:
        edges[device_map[l.from_device.pk]].add(device_map[l.to_device.pk])
        edges[device_map[l.to_device.pk]].add(device_map[l.from_device.pk])


    similar_connections = defaultdict(list)

    for device, connections in edges.iteritems():
        similar_connections[tuple(connections)].append(device)


    for connections, from_devices in similar_connections.iteritems():
        if len(from_devices) > 0 and from_devices[0].role == "host":
            racks.append(from_devices)

    tiers = defaultdict(list)

    for device in devices:
        if getattr(device, 'tier', None):
            pass
        elif device.role == "leaf":
            device.tier = 1
        elif device.role == "spine":
            device.tier = 2
        elif device.role == "host":
            device.tier = 0
        else:
            device.tier = 3
        tiers[device.tier].append(device)

    for rack in racks:
        rack.sort(key=lambda x: x.name)

    racks.sort(key=lambda x: x[0].name)

    for tier in tiers.values():
        tier.sort(key=lambda x: x.name)

    for device in devices:
        print device, getattr(device, 'tier', None)
        if getattr(device, 'tier', None) is None:
            device.y = 0
            device.x = 0
        else:
            device.y = SPACING * 3 - device.tier * SPACING
            device.x = 0 - (len(tiers[device.tier]) * SPACING) / 2 + tiers[device.tier].index(device) * SPACING
        device.save()

    for j, rack in enumerate(racks):
        x = 0 - (len(racks) * SPACING) / 2 + j * SPACING
        for i, device in enumerate(rack):
            device.x = x
            device.y = SPACING * 3 + i * RACK_SPACING
            device.save()

    send_snapshot(Group("topology-%s" % topology_id), topology_id)


def parse_topology_id(data):
    topology_id = data.get('topology_id', ['null'])
    try:
        topology_id = int(topology_id[0])
    except ValueError:
        topology_id = None
    if not topology_id:
        topology_id = None
    return topology_id


def parse_inventory_id(data):
    inventory_id = data.get('inventory_id', ['null'])
    try:
        inventory_id = int(inventory_id[0])
    except ValueError:
        inventory_id = None
    if not inventory_id:
        inventory_id = None
    return inventory_id

# Persistence


class _Persistence(object):

    def handle(self, message):
        topology_id = message.get('topology')
        assert topology_id is not None, "No topology_id"
        client_id = message.get('client')
        assert client_id is not None, "No client_id"
        data = json.loads(message['text'])
        if isinstance(data[1], list):
            print "no sender"
            return
        if isinstance(data[1], dict) and client_id != data[1].get('sender'):
            logger.error("client_id mismatch expected: %s actual %s", client_id, data[1].get('sender'))
            logger.error(pformat(data))
            return
        message_type = data[0]
        message_value = data[1]
        try:
            message_type_id = MessageType.objects.get(name=message_type).pk
        except ObjectDoesNotExist:
            logger.warning("Unsupported message %s: no message type", message_type)
            return
        TopologyHistory(topology_id=topology_id,
                        client_id=client_id,
                        message_type_id=message_type_id,
                        message_id=data[1].get('message_id', 0),
                        message_data=message['text']).save()
        handler = self.get_handler(message_type)
        if handler is not None:
            handler(message_value, topology_id, client_id)
        else:
            logger.warning("Unsupported message %s: no handler", message_type)

    def get_handler(self, message_type):
        return getattr(self, "on{0}".format(message_type), None)

    def onDeviceCreate(self, device, topology_id, client_id):
        device = transform_dict(dict(x='x',
                                     y='y',
                                     name='name',
                                     type='type',
                                     id='id',
                                     host_id='host_id'), device)
        logger.info("Device %s", device)
        print ("Device %s" % device)
        d, _ = Device.objects.get_or_create(topology_id=topology_id, id=device['id'], defaults=device)
        d.x = device['x']
        d.y = device['y']
        d.type = device['type']
        d.host_id = device['host_id']
        d.save()
        (Topology.objects
                 .filter(topology_id=topology_id, device_id_seq__lt=device['id'])
                 .update(device_id_seq=device['id']))

    def onDeviceDestroy(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).delete()

    def onDeviceMove(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).update(x=device['x'], y=device['y'])

    def onDeviceLabelEdit(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).update(name=device['name'])
        for pk in Device.objects.filter(topology_id=topology_id, id=device['id']).values_list('pk', flat=True):
            for db in DataBinding.objects.filter(primary_key_id=pk,
                                                 table="Device",
                                                 field="name").values('sheet__client_id',
                                                                      'sheet__name',
                                                                      'column',
                                                                      'row'):
                message = ['TableCellEdit', dict(sender=0,
                                                 msg_type="TableCellEdit",
                                                 sheet=db['sheet__name'],
                                                 col=db['column'] + 1, 
                                                 row=db['row'] + 2, 
                                                 new_value=device['name'],
                                                 old_value=device['previous_name'])]
                logger.info("Sending message %r", message)
                Group("topology-%s-client-%s" % (topology_id, db['sheet__client_id'])).send({"text": json.dumps(message)})


    def onInterfaceLabelEdit(self, interface, topology_id, client_id):
        (Interface.objects
                  .filter(device__topology_id=topology_id,
                          id=interface['id'],
                          device__id=interface['device_id'])
                  .update(name=interface['name']))

    def onLinkLabelEdit(self, link, topology_id, client_id):
        Link.objects.filter(from_device__topology_id=topology_id, id=link['id']).update(name=link['name'])

    def onInterfaceCreate(self, interface, topology_id, client_id):
        Interface.objects.get_or_create(device_id=Device.objects.get(id=interface['device_id'],
                                                                     topology_id=topology_id).pk,
                                        id=interface['id'],
                                        defaults=dict(name=interface['name']))
        (Device.objects
               .filter(id=interface['device_id'],
                       topology_id=topology_id,
                       interface_id_seq__lt=interface['id'])
               .update(interface_id_seq=interface['id']))

    def onLinkCreate(self, link, topology_id, client_id):
        device_map = dict(Device.objects
                                .filter(topology_id=topology_id, id__in=[link['from_device_id'], link['to_device_id']])
                                .values_list('id', 'pk'))
        Link.objects.get_or_create(id=link['id'],
                                   name=link['name'],
                                   from_device_id=device_map[link['from_device_id']],
                                   to_device_id=device_map[link['to_device_id']],
                                   from_interface_id=Interface.objects.get(device_id=device_map[link['from_device_id']],
                                                                           id=link['from_interface_id']).pk,
                                   to_interface_id=Interface.objects.get(device_id=device_map[link['to_device_id']],
                                                                         id=link['to_interface_id']).pk)
        (Topology.objects
                 .filter(topology_id=topology_id, link_id_seq__lt=link['id'])
                 .update(link_id_seq=link['id']))

    def onLinkDestroy(self, link, topology_id, client_id):
        device_map = dict(Device.objects
                                .filter(topology_id=topology_id, id__in=[link['from_device_id'], link['to_device_id']])
                                .values_list('id', 'pk'))
        Link.objects.filter(id=link['id'],
                            from_device_id=device_map[link['from_device_id']],
                            to_device_id=device_map[link['to_device_id']],
                            from_interface_id=Interface.objects.get(device_id=device_map[link['from_device_id']],
                                                                    id=link['from_interface_id']).pk,
                            to_interface_id=Interface.objects.get(device_id=device_map[link['to_device_id']],
                                                                  id=link['to_interface_id']).pk).delete()

    def onProcessCreate(self, process, topology_id, client_id):
        Process.objects.get_or_create(device_id=Device.objects.get(id=process['device_id'],
                                                                   topology_id=topology_id).pk,
                                      id=process['id'],
                                      defaults=dict(name=process['name'], type=process['type']))
        (Device.objects
               .filter(id=process['device_id'],
                       topology_id=topology_id,
                       interface_id_seq__lt=process['id'])
               .update(interface_id_seq=process['id']))

    def onStreamCreate(self, stream, topology_id, client_id):
        device_map = dict(Device.objects
                                .filter(topology_id=topology_id, id__in=[stream['from_id'], stream['to_id']])
                                .values_list('id', 'pk'))
        logger.info("onStreamCreate %s", stream)
        Stream.objects.get_or_create(id=stream['id'],
                                     label='',
                                     from_device_id=device_map[stream['from_id']],
                                     to_device_id=device_map[stream['to_id']])
        (Topology.objects
                 .filter(topology_id=topology_id, stream_id_seq__lt=stream['id'])
                 .update(stream_id_seq=stream['id']))

    def onCopySite(self, site, topology_id, client_id):
        site_toolbox, _ = Toolbox.objects.get_or_create(name="Site")
        ToolboxItem(toolbox=site_toolbox, data=json.dumps(site['site'])).save()

    def onDeviceSelected(self, message_value, topology_id, client_id):
        'Ignore DeviceSelected messages'
        pass

    def onDeviceUnSelected(self, message_value, topology_id, client_id):
        'Ignore DeviceSelected messages'
        pass

    def onLinkSelected(self, message_value, topology_id, client_id):
        'Ignore LinkSelected messages'
        pass

    def onLinkUnSelected(self, message_value, topology_id, client_id):
        'Ignore LinkSelected messages'
        pass

    def onUndo(self, message_value, topology_id, client_id):
        undo_persistence.handle(message_value['original_message'], topology_id, client_id)

    def onRedo(self, message_value, topology_id, client_id):
        redo_persistence.handle(message_value['original_message'], topology_id, client_id)

    def onMultipleMessage(self, message_value, topology_id, client_id):
        for message in message_value['messages']:
            handler = self.get_handler(message['msg_type'])
            if handler is not None:
                handler(message, topology_id, client_id)
            else:
                logger.warning("Unsupported message %s", message['msg_type'])

    def onLayout(self, message_value, topology_id, client_id):
        # circular_layout(topology_id)
        # grid_layout(topology_id)
        tier_layout(topology_id)


    def onCoverageRequest(self, coverage, topology_id, client_id):
        pass

    def onTestResult(self, test_result, topology_id, client_id):
        xyz, _, rest = test_result['code_under_test'].partition('-')
        commits_since, _, commit_hash = rest.partition('-')
        commit_hash = commit_hash.strip('g')
        
        print (xyz)
        print (commits_since)
        print (commit_hash)

        x, y, z = [int(i) for i in xyz.split('.')]

        print (x, y, z)

        code_under_test, _ = CodeUnderTest.objects.get_or_create(version_x=x,
                                                                 version_y=y,
                                                                 version_z=z,
                                                                 commits_since=int(commits_since),
                                                                 commit_hash=commit_hash)

        print (code_under_test)

        tr = TestResult(id=test_result['id'],
                        result_id=Result.objects.get(name=test_result['result']).pk,
                        test_case_id=TestCase.objects.get(name=test_result['name']).pk,
                        code_under_test_id=code_under_test.pk,
                        client_id=client_id,
                        time=parse_datetime(test_result['date']))
        tr.save()
        print (tr.pk)


    def onCoverage(self, coverage, topology_id, client_id):
        Coverage(test_result_id=TestResult.objects.get(id=coverage['result_id'], client_id=client_id).pk,
                 coverage_data=json.dumps(coverage['coverage'])).save()

    def onStartRecording(self, recording, topology_id, client_id):
        pass

    def onStopRecording(self, recording, topology_id, client_id):
        pass

    def write_event(self, event, topology_id, client_id):
        if event.get('save', True):
            EventTrace(trace_session_id=event['trace_id'],
                       event_data=json.dumps(event),
                       message_id=event['message_id'],
                       client_id=client_id).save()

    onViewPort = write_event
    onMouseEvent = write_event
    onTouchEvent = write_event
    onMouseWheelEvent = write_event
    onKeyEvent = write_event

    def onGroupCreate(self, group, topology_id, client_id):
        logger.info("GroupCreate %s %s %s", group['id'], group['name'], group['type'])
        group = transform_dict(dict(x1='x1',
                                    y1='y1',
                                    x2='x2',
                                    y2='y2',
                                    name='name',
                                    id='id',
                                    type='type'), group)
        d, _ = DeviceGroup.objects.get_or_create(topology_id=topology_id, id=group['id'], defaults=group)
        d.x1 = group['x1']
        d.y1 = group['y1']
        d.x2 = group['x2']
        d.y2 = group['y2']
        d.type = group['type']
        d.save()
        (Topology.objects
                 .filter(topology_id=topology_id, group_id_seq__lt=group['id'])
                 .update(group_id_seq=group['id']))

    def onGroupDestroy(self, group, topology_id, client_id):
        DeviceGroup.objects.filter(topology_id=topology_id, id=group['id']).delete()

    def onGroupLabelEdit(self, group, topology_id, client_id):
        DeviceGroup.objects.filter(topology_id=topology_id, id=group['id']).update(name=group['name'])

    def onGroupMove(self, group, topology_id, client_id):
        DeviceGroup.objects.filter(topology_id=topology_id, id=group['id']).update(x1=group['x1'],
                                                                                   y1=group['y1'],
                                                                                   x2=group['x2'],
                                                                                   y2=group['y2'])

    def onGroupMembership(self, group_membership, topology_id, client_id):
        members = set(group_membership['members'])
        group = DeviceGroup.objects.get(topology_id=topology_id, id=group_membership['id'])
        existing = set(GroupDeviceMap.objects.filter(group=group).values_list('device__id', flat=True))
        new = members - existing
        removed = existing - members

        GroupDeviceMap.objects.filter(group__group_id=group.group_id,
                                      device__id__in=list(removed)).delete()

        device_map = dict(Device.objects.filter(topology_id=topology_id, id__in=list(new)).values_list('id', 'device_id'))
        new_entries = []
        for i in new:
            new_entries.append(GroupDeviceMap(group=group,
                                              device_id=device_map[i]))
        if new_entries:
            GroupDeviceMap.objects.bulk_create(new_entries)

    def onFSMTrace(self, message_value, diagram_id, client_id):
        FSMTrace(trace_session_id=message_value['trace_id'],
                 fsm_name=message_value['fsm_name'],
                 from_state=message_value['from_state'],
                 to_state=message_value['to_state'],
                 order=message_value['order'],
                 client_id=client_id,
                 message_type=message_value['recv_message_type'] or "none").save()

    def onSnapshot(self, snapshot, topology_id, client_id):
        TopologySnapshot(trace_session_id=snapshot['trace_id'],
                         snapshot_data=json.dumps(snapshot),
                         order=snapshot['order'],
                         client_id=client_id,
                         topology_id=topology_id).save()


persistence = _Persistence()


class _UndoPersistence(object):

    def handle(self, message, topology_id, client_id):
        message_type = message[0]
        message_value = message[1]
        TopologyHistory.objects.filter(topology_id=topology_id,
                                       client_id=message_value['sender'],
                                       message_id=message_value['message_id']).update(undone=True)
        handler = getattr(self, "on{0}".format(message_type), None)
        if handler is not None:
            handler(message_value, topology_id, client_id)
        else:
            logger.warning("Unsupported undo message %s", message_type)

    def onSnapshot(self, snapshot, topology_id, client_id):
        pass

    def onDeviceCreate(self, device, topology_id, client_id):
        persistence.onDeviceDestroy(device, topology_id, client_id)

    def onDeviceDestroy(self, device, topology_id, client_id):
        inverted = device.copy()
        inverted['type'] = device['previous_type']
        inverted['name'] = device['previous_name']
        inverted['x'] = device['previous_x']
        inverted['y'] = device['previous_y']
        persistence.onDeviceCreate(inverted, topology_id, client_id)

    def onDeviceMove(self, device, topology_id, client_id):
        inverted = device.copy()
        inverted['x'] = device['previous_x']
        inverted['y'] = device['previous_y']
        persistence.onDeviceMove(inverted, topology_id, client_id)

    def onDeviceLabelEdit(self, device, topology_id, client_id):
        inverted = device.copy()
        inverted['name'] = device['previous_name']
        persistence.onDeviceLabelEdit(inverted, topology_id, client_id)

    def onLinkCreate(self, link, topology_id, client_id):
        persistence.onLinkDestroy(link, topology_id, client_id)

    def onLinkDestroy(self, link, topology_id, client_id):
        persistence.onLinkCreate(link, topology_id, client_id)

    def onDeviceSelected(self, message_value, topology_id, client_id):
        'Ignore DeviceSelected messages'
        pass

    def onDeviceUnSelected(self, message_value, topology_id, client_id):
        'Ignore DeviceSelected messages'
        pass

    def onUndo(self, message_value, topology_id, client_id):
        pass


undo_persistence = _UndoPersistence()


class _RedoPersistence(object):

    def handle(self, message, topology_id, client_id):
        message_type = message[0]
        message_value = message[1]
        TopologyHistory.objects.filter(topology_id=topology_id,
                                       client_id=message_value['sender'],
                                       message_id=message_value['message_id']).update(undone=False)
        handler_name = "on{0}".format(message_type)
        handler = getattr(self, handler_name, getattr(persistence, handler_name, None))
        if handler is not None:
            handler(message_value, topology_id, client_id)
        else:
            logger.warning("Unsupported redo message %s", message_type)

    def onDeviceSelected(self, message_value, topology_id, client_id):
        'Ignore DeviceSelected messages'
        pass

    def onDeviceUnSelected(self, message_value, topology_id, client_id):
        'Ignore DeviceSelected messages'
        pass

    def onUndo(self, message_value, topology_id, client_id):
        'Ignore Undo messages'
        pass

    def onRedo(self, message_value, topology_id, client_id):
        'Ignore Redo messages'
        pass


redo_persistence = _RedoPersistence()


class _Discovery(object):

    def handle(self, message):
        topology_id = message.get('topology')
        data = json.loads(message['text'])
        message_type = data[0]
        message_value = data[1]
        handler = self.get_handler(message_type)
        if handler is not None:
            handler(message_value, topology_id)
        else:
            logger.warning("Unsupported discovery message %s", message_type)

    def get_handler(self, message_type):
        return getattr(self, "on{0}".format(message_type), None)

    def onFacts(self, message, topology_id):
        send_updates = False
        logger.info("onFacts message key %s", message['key'])
        #logger.info("onFacts message %s", pformat(message))
        device_name = message['key']
        updates = MultipleMessage('MultipleMessage', [])
        try:
            device = Device.objects.get(topology_id=topology_id, name=device_name)
        except ObjectDoesNotExist:
            logger.info("onFacts Could not find %s in topology %s", device_name, topology_id)
            return

        try:
            interfaces = dpath.util.get(message, '/value/ansible_net_neighbors')
            logger.info(pformat(interfaces))
        except KeyError:
            interfaces = {}
        logger.info("onFacts %s: ", pformat(interfaces))
        """
        ansible_net_neighbors example:
         {u'eth1': [{u'host': u'Spine1', u'port': u'eth3'}],
         u'eth2': [{u'host': u'Spine2', u'port': u'eth3'}],
         u'eth3': [{u'host': u'Host2', u'port': u'eth1'}]}
            """
        for interface_name, neighbors in interfaces.iteritems():
            logger.info("interface_name %s neighbors %s", interface_name, neighbors)
            interface, created = Interface.objects.get_or_create(device_id=device.pk,
                                                                 name=interface_name,
                                                                 defaults=dict(id=0))
            if created:
                interface.id = interface.pk
                interface.save()
                updates.messages.append(InterfaceCreate('InterfaceCreate',
                                                        0,
                                                        interface.device.id,
                                                        interface.id,
                                                        interface.name))
                send_updates = True
                logger.info("Created interface %s", interface)


            for neighbor in neighbors:
                logger.info("neighbor %s", neighbor)
                connected_interface = None
                connected_device = None
                neighbor_name = neighbor.get('host')
                if not neighbor_name:
                    continue
                try:
                    connected_device = Device.objects.get(topology_id=topology_id, name=neighbor_name)
                except ObjectDoesNotExist:
                    continue

                logger.info("neighbor %s %s", neighbor_name, connected_device.pk)

                remote_interface_name = neighbor.get('port')

                connected_interface, created = Interface.objects.get_or_create(device_id=connected_device.pk,
                                                                               name=remote_interface_name,
                                                                               defaults=dict(id=0))
                if created:
                    connected_interface.id = connected_interface.pk
                    connected_interface.save()
                    updates.messages.append(InterfaceCreate('InterfaceCreate',
                                                            0,
                                                            connected_interface.device.id,
                                                            connected_interface.id,
                                                            connected_interface.name))
                    logger.info("Created interface %s", connected_interface)
                    send_updates = True

                if connected_device and connected_interface:
                    exists = Link.objects.filter(Q(from_device_id=device.pk,
                                                   to_device_id=connected_device.pk,
                                                   from_interface_id=interface.pk,
                                                   to_interface_id=connected_interface.pk) |
                                                 Q(from_device_id=connected_device.pk,
                                                   to_device_id=device.pk,
                                                   from_interface_id=connected_interface.pk,
                                                   to_interface_id=interface.pk)).count() > 0
                    if not exists:
                        link = Link(from_device_id=device.pk,
                                    to_device_id=connected_device.pk,
                                    from_interface_id=interface.pk,
                                    to_interface_id=connected_interface.pk,
                                    id=0)

                        link.save()
                        link.id = link.pk
                        link.save()
                        updates.messages.append(LinkCreate('LinkCreate',
                                                           0,
                                                           link.id,
                                                           link.name,
                                                           link.from_device.id,
                                                           link.to_device.id,
                                                           link.from_interface.id,
                                                           link.to_interface.id))
                        logger.info("Created link %s", link)
                        send_updates = True

        if send_updates:
            logger.info("onFacts send_updates")
            channel = Group("topology-%s" % topology_id)
            channel.send({"text": json.dumps([updates.msg_type, to_dict(updates)])})


discovery = _Discovery()

# Ansible Connection Events


@channel_session
def ansible_connect(message):
    data = urlparse.parse_qs(message.content['query_string'])
    topology_id = parse_topology_id(data)
    message.channel_session['topology_id'] = topology_id


@channel_session
def ansible_message(message):
    # Channel('console_printer').send({"text": message['text']})
    Group("topology-%s" % message.channel_session['topology_id']).send({"text": message['text']})
    Channel('discovery').send({"text": message['text'],
                               "topology": message.channel_session['topology_id']})


@channel_session
def ansible_disconnect(message):
    pass


# UI Channel Events

@channel_session
def ws_connect(message):
    # Accept connection
    data = urlparse.parse_qs(message.content['query_string'])
    inventory_id = parse_inventory_id(data)
    topology_ids = list(TopologyInventory.objects.filter(inventory_id=inventory_id).values_list('topology_id', flat=True))
    print ("topology_ids", topology_ids)
    topology_id = 0
    if len(topology_ids) > 0:
        topology_id = topology_ids[0]
    print ("topology_id", topology_id)
    if topology_id:
        topology = Topology.objects.get(topology_id=topology_id)
    else:
        topology = Topology(name="topology", scale=1.0, panX=0, panY=0)
        topology.save()
        TopologyInventory(inventory_id=inventory_id, topology_id=topology.topology_id).save()
    topology_id = topology.topology_id
    message.channel_session['topology_id'] = topology_id
    Group("topology-%s" % topology_id).add(message.reply_channel)
    client = Client()
    client.save()
    message.channel_session['client_id'] = client.pk
    message.reply_channel.send({"text": json.dumps(["id", client.pk])})
    message.reply_channel.send({"text": json.dumps(["topology_id", topology_id])})
    topology_data = transform_dict(dict(topology_id='topology_id',
                                        name='name',
                                        panX='panX',
                                        panY='panY',
                                        scale='scale',
                                        link_id_seq='link_id_seq',
                                        device_id_seq='device_id_seq',
                                        group_id_seq='group_id_seq'), topology.__dict__)

    message.reply_channel.send({"text": json.dumps(["Topology", topology_data])})
    send_snapshot(message.reply_channel, topology_id)
    send_history(message.reply_channel, topology_id)
    send_toolboxes(message.reply_channel)
    send_tests(message.reply_channel)


def send_toolboxes(channel):
    for toolbox_item in ToolboxItem.objects.filter(toolbox__name__in=['Process', 'Device', 'Rack', 'Site']).values('toolbox__name', 'data'):
        item = dict(toolbox_name=toolbox_item['toolbox__name'],
                    data=toolbox_item['data'])
        channel.send({"text": json.dumps(["ToolboxItem", item])})


def send_tests(channel):
    for name, test_case_data in TestCase.objects.all().values_list('name', 'test_case_data'):
        channel.send({"text": json.dumps(["TestCase", [name, json.loads(test_case_data)]])})


def send_snapshot(channel, topology_id):
    interfaces = defaultdict(list)
    processes = defaultdict(list)

    for i in (Interface.objects
              .filter(device__topology_id=topology_id)
              .values()):
        interfaces[i['device_id']].append(i)
    for i in (Process.objects
              .filter(device__topology_id=topology_id)
              .values()):
        processes[i['device_id']].append(i)
    devices = list(Device.objects
                         .filter(topology_id=topology_id).values())
    for device in devices:
        device['interfaces'] = interfaces[device['device_id']]
        device['processes'] = processes[device['device_id']]

    links = [dict(id=x['id'],
                  name=x['name'],
                  from_device_id=x['from_device__id'],
                  to_device_id=x['to_device__id'],
                  from_interface_id=x['from_interface__id'],
                  to_interface_id=x['to_interface__id'])
             for x in list(Link.objects
                               .filter(Q(from_device__topology_id=topology_id) |
                                       Q(to_device__topology_id=topology_id))
                               .values('id',
                                       'name',
                                       'from_device__id',
                                       'to_device__id',
                                       'from_interface__id',
                                       'to_interface__id'))]
    groups = list(DeviceGroup.objects
                             .filter(topology_id=topology_id).values())
    group_map = {g['id']: g for g in groups}
    for group_id, device_id in GroupDeviceMap.objects.filter(group__topology_id=topology_id).values_list('group__id', 'device__id'):
        if 'members' not in group_map[group_id]:
            group_map[group_id]['members'] = [device_id]
        else:
            group_map[group_id]['members'].append(device_id)

    streams = [dict(id=x['id'],
                    label=x['label'],
                    from_id=x['from_device__id'],
                    to_id=x['to_device__id'])
               for x in list(Stream.objects
                                   .filter(Q(from_device__topology_id=topology_id) |
                                           Q(to_device__topology_id=topology_id)).values('id',
                                                                                         'label',
                                                                                         'from_device__id',
                                                                                         'to_device__id'))]

    snapshot = dict(sender=0,
                    devices=devices,
                    links=links,
                    groups=groups,
                    streams=streams)
    channel.send({"text": json.dumps(["Snapshot", snapshot])})


def send_history(channel, topology_id):
    history = list(TopologyHistory.objects
                                  .filter(topology_id=topology_id)
                                  .exclude(message_type__name__in=HISTORY_MESSAGE_IGNORE_TYPES)
                                  .exclude(undone=True)
                                  .order_by('pk')
                                  .values_list('message_data', flat=True)[:1000])
    channel.send({"text": json.dumps(["History", history])})


@channel_session
def ws_message(message):
    # Send to debug printer
    # Channel('console_printer').send({"text": message['text']})
    # Send to all clients editing the topology
    Group("topology-%s" % message.channel_session['topology_id']).send({"text": message['text']})
    # Send to persistence handler
    Channel('persistence').send({"text": message['text'],
                                 "topology": message.channel_session['topology_id'],
                                 "client": message.channel_session['client_id']})


@channel_session
def ws_disconnect(message):
    if 'topology_id' in message.channel_session:
        Group("topology-%s" % message.channel_session['topology_id']).discard(message.reply_channel)


def console_printer(message):
    print message['text']  # pragma: no cover

# Tester channel events


@channel_session
def tester_connect(message):
    data = urlparse.parse_qs(message.content['query_string'])
    topology_id = parse_topology_id(data)
    message.channel_session['topology_id'] = topology_id
    client = Client()
    client.save()
    message.channel_session['client_id'] = client.pk
    message.reply_channel.send({"text": json.dumps(["id", client.pk])})
    message.reply_channel.send({"text": json.dumps(["topology_id", topology_id])})


@channel_session
def tester_message(message):
    # Channel('console_printer').send({"text": message['text']})
    Group("topology-%s" % message.channel_session['topology_id']).send({"text": message['text']})
    Channel('persistence').send({"text": message['text'],
                                 "topology": message.channel_session['topology_id'],
                                 "client": message.channel_session['client_id']})


@channel_session
def tester_disconnect(message):
    pass

# Tables UI channel events


def make_sheet(data, column_headers=[]):

    sheet = []

    if len(data):
        n_columns = max([len(x) for x in data]) - 1
    else:
        n_columns = 0

    row_i = 0
    sheet.append([dict(value=x, editable=False) for x in list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")[0:n_columns]])
    row_i += 1
    if column_headers:
        sheet.append([dict(value=row_i, editable=False)] + [dict(value=x, editable=False) for x in column_headers])
        row_i += 1
    for row in data:
        sheet_row = [dict(value=row_i, editable=False)]
        row_i += 1
        sheet_row.extend([dict(value=x, editable=True, col=i, row=row_i) for i, x in enumerate(row[1:])])
        sheet.append(sheet_row)
    return sheet



def make_bindings(sheet_id, klass, filter_q, values_list, order_by):

    values_list = ['pk'] + values_list
    data = list(klass.objects.filter(**filter_q).values_list(*values_list).order_by(*order_by))

    data_types = set()

    for row in data:
        for cell in row:
            data_types.add(type(cell).__name__)

    data_type_map = dict()

    logger.info(repr(data_types))

    for dt in list(data_types):
        data_type_map[dt] = DataType.objects.get_or_create(type_name=dt)[0].pk

    logger.info(repr(data_type_map))

    bindings = []

    for row_i, row in enumerate(data):
        pk = row[0]
        for col_i, cell in enumerate(row[1:]):
            field = values_list[col_i + 1]
            if '__' in field:
                continue
            logger.info("make_bindings %s %s %s %s %s %s %s", sheet_id, klass.__name__, pk, col_i, row_i, field, data_type_map[type(cell).__name__])
            bindings.append(DataBinding.objects.get_or_create(sheet_id=sheet_id,
                                                              column=col_i,
                                                              row=row_i,
                                                              table=klass.__name__,
                                                              primary_key_id=pk,
                                                              field=field,
                                                              data_type_id=data_type_map[type(cell).__name__])[0])
    return data



@channel_session
def tables_connect(message):
    data = urlparse.parse_qs(message.content['query_string'])
    topology_id = parse_topology_id(data)
    message.channel_session['topology_id'] = topology_id
    client = Client()
    client.save()
    Group("topology-%s-client-%s" % (topology_id, client.pk)).add(message.reply_channel)
    message.channel_session['client_id'] = client.pk
    message.reply_channel.send({"text": json.dumps(["id", client.pk])})
    message.reply_channel.send({"text": json.dumps(["topology_id", topology_id])})

    device_sheet, _ = DataSheet.objects.get_or_create(topology_id=topology_id, client_id=client.pk, name="Devices")
    data = make_bindings(device_sheet.pk, Device, dict(topology_id=topology_id), ['name'], ['name'])
    message.reply_channel.send({"text": json.dumps(["sheet", dict(name="Devices", data=make_sheet(data, ['Device Name']))])})

    interface_sheet, _ = DataSheet.objects.get_or_create(topology_id=topology_id, client_id=client.pk, name="Interfaces")
    data = make_bindings(interface_sheet.pk, Interface, dict(device__topology_id=topology_id), ['device__name', 'name'], ['device__name', 'name'])
    message.reply_channel.send({"text": json.dumps(["sheet", dict(name="Interfaces", data=make_sheet(data, ['Device Name', 'Interface Name']))])})

    group_sheet, _ = DataSheet.objects.get_or_create(topology_id=topology_id, client_id=client.pk, name="Groups")
    data = make_bindings(group_sheet.pk, DeviceGroup, dict(topology_id=topology_id), ['name'], ['name'])
    message.reply_channel.send({"text": json.dumps(["sheet", dict(name="Groups", data=make_sheet(data, ['Group Name']))])})


def device_label_edit(o):
    d = transform_dict(dict(name='name',
                            id='id',
                            old_value='previous_name'), o.__dict__)
    d['msg_type'] = 'DeviceLabelEdit'
    return ['DeviceLabelEdit', d]


def group_label_edit(o):
    d = transform_dict(dict(name='name',
                            id='id',
                            old_value='previous_name'), o.__dict__)
    d['msg_type'] = 'GroupLabelEdit'
    return ['GroupLabelEdit', d]


def interface_label_edit(o):
    d = o.__dict__
    d['device_id'] = o.device.id
    d = transform_dict(dict(name='name',
                            id='id',
                            device_id='device_id',
                            old_value='previous_name'), o.__dict__)
    d['msg_type'] = 'InterfaceLabelEdit'
    return ['InterfaceLabelEdit', d]


@channel_session
def tables_message(message):
    data = json.loads(message['text'])
    logger.info(data[0])
    logger.info(data[1])

    data_type_mapping = {'unicode': unicode,
                         'int': int}


    table_mapping = {'Device': Device,
                     'Interface': Interface,
                     'Group': DeviceGroup}


    transformation_mapping = {('Device', 'name'): device_label_edit,
                              ('Interface', 'name'): interface_label_edit,
                              ('Group', 'name'): group_label_edit}


    if data[0] == "TableCellEdit":

        topology_id = message.channel_session['topology_id']
        group_channel = Group("topology-%s" % topology_id)
        client_id = message.channel_session['client_id']
        data_sheet = DataSheet.objects.get(topology_id=topology_id, client_id=client_id, name=data[1]['sheet']).pk
        logger.info("DataSheet %s", data_sheet)

        data_bindings = DataBinding.objects.filter(sheet_id=data_sheet,
                                                   column=data[1]['col'] - 1,
                                                   row=data[1]['row'] - 2)

        logger.info("Found %s bindings", data_bindings.count())
        logger.info(repr(data_bindings.values('table', 'data_type__type_name', 'field', 'primary_key_id')))

        for table, data_type, field, pk in data_bindings.values_list('table', 'data_type__type_name', 'field', 'primary_key_id'):
            new_value = data_type_mapping[data_type](data[1]['new_value'])
            old_value = data_type_mapping[data_type](data[1]['old_value'])
            logger.info("Updating %s", table_mapping[table].objects.filter(pk=pk).values())
            table_mapping[table].objects.filter(pk=pk).update(**{field: new_value})
            logger.info("Updated %s", table_mapping[table].objects.filter(pk=pk).count())

            for o in table_mapping[table].objects.filter(pk=pk):
                o.old_value = old_value
                message = transformation_mapping[(table, field)](o)
                message[1]['sender'] = 0
                logger.info("Sending %r", message)
                group_channel.send({"text": json.dumps(message)})



@channel_session
def tables_disconnect(message):
    pass
