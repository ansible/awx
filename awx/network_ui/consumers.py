# In consumers.py
from channels import Group, Channel
from channels.sessions import channel_session
from awx.network_ui.models import Topology, Device, Link, Client, TopologyHistory, MessageType, Interface
from awx.network_ui.serializers import yaml_serialize_topology
import urlparse
from django.db.models import Q
from collections import defaultdict
from django.conf import settings
import math
import random

from awx.network_ui.utils import transform_dict
from pprint import pprint
import dpath.util

import json
import time
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
settings.RECORDING = False


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

    pprint(devices)

    similar_connections = defaultdict(list)

    for device, connections in edges.iteritems():
        similar_connections[tuple(connections)].append(device)

    pprint(dict(**similar_connections))

    for connections, from_devices in similar_connections.iteritems():
        if len(from_devices) > 0 and from_devices[0].role == "host":
            racks.append(from_devices)

    pprint(racks)
    pprint(devices)

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

    pprint(tiers)

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
            device.y = SPACING * 3 +  i * RACK_SPACING
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
            print "client_id mismatch expected:", client_id, "actual:", data[1].get('sender')
            return
        message_type = data[0]
        message_value = data[1]
        message_type_id = MessageType.objects.get_or_create(name=message_type)[0].pk
        TopologyHistory(topology_id=topology_id,
                        client_id=client_id,
                        message_type_id=message_type_id,
                        message_id=data[1].get('message_id', 0),
                        message_data=message['text']).save()
        handler = self.get_handler(message_type)
        if handler is not None:
            handler(message_value, topology_id, client_id)
        else:
            print "Unsupported message ", message_type

    def get_handler(self, message_type):
        return getattr(self, "on{0}".format(message_type), None)

    def onDeviceCreate(self, device, topology_id, client_id):
        device = transform_dict(dict(x='x',
                                     y='y',
                                     name='name',
                                     type='type',
                                     id='id'), device)
        d, _ = Device.objects.get_or_create(topology_id=topology_id, id=device['id'], defaults=device)
        d.x = device['x']
        d.y = device['y']
        d.type = device['type']
        d.save()

    def onDeviceDestroy(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).delete()

    def onDeviceMove(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).update(x=device['x'], y=device['y'])

    def onDeviceLabelEdit(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).update(name=device['name'])

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
                print "Unsupported message ", message['msg_type']

    def onDeploy(self, message_value, topology_id, client_id):
        Group("workers").send({"text": json.dumps(["Deploy", topology_id, yaml_serialize_topology(topology_id)])})

    def onDestroy(self, message_value, topology_id, client_id):
        Group("workers").send({"text": json.dumps(["Destroy", topology_id])})

    def onDiscover(self, message_value, topology_id, client_id):
        Group("workers").send({"text": json.dumps(["Discover", topology_id, yaml_serialize_topology(topology_id)])})

    def onLayout(self, message_value, topology_id, client_id):
        # circular_layout(topology_id)
        # grid_layout(topology_id)
        tier_layout(topology_id)

    def onCoverageRequest(self, coverage, topology_id, client_id):
        pass

    def onCoverage(self, coverage, topology_id, client_id):
        with open("coverage/coverage{0}.json".format(int(time.time())), "w") as f:
            f.write(json.dumps(coverage['coverage']))

    def onStartRecording(self, recording, topology_id, client_id):
        settings.RECORDING = True

    def onStopRecording(self, recording, topology_id, client_id):
        settings.RECORDING = False

    def write_event(self, event, topology_id, client_id):
        if settings.RECORDING and event.get('save', True):
            with open("recording.log", "a") as f:
                f.write(json.dumps(event))
                f.write("\n")

    onViewPort = write_event
    onMouseEvent = write_event
    onTouchEvent = write_event
    onMouseWheelEvent = write_event
    onKeyEvent = write_event


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
            print "Unsupported undo message ", message_type

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
            print "Unsupported redo message ", message_type

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
            print "Unsupported message ", message_type

    def get_handler(self, message_type):
        return getattr(self, "on{0}".format(message_type), None)

    def onFacts(self, message, topology_id):
        send_updates = False
        print message['key']
        name = message['key']
        device, created = Device.objects.get_or_create(topology_id=topology_id,
                                                       name=name,
                                                       defaults=dict(x=0,
                                                                     y=0,
                                                                     type="switch",
                                                                     id=0))

        if created:
            device.id = device.pk
            device.save()
            send_updates = True
            print "Created device ", device

        interfaces = dpath.util.get(message, '/value/ansible_local/lldp/lldp') or []
        for interface in interfaces:
            pprint(interface)
            for inner_interface in interface.get('interface', []):
                name = inner_interface.get('name')
                if not name:
                    continue
                interface, created = Interface.objects.get_or_create(device_id=device.pk,
                                                                     name=name,
                                                                     defaults=dict(id=0))
                if created:
                    interface.id = interface.pk
                    interface.save()
                    send_updates = True
                    print "Created interface ", interface

                connected_interface = None
                connected_device = None

                for chassis in inner_interface.get('chassis', []):
                    name = chassis.get('name', [{}])[0].get('value')
                    if not name:
                        continue
                    connected_device, created = Device.objects.get_or_create(topology_id=topology_id,
                                                                             name=name,
                                                                             defaults=dict(x=0,
                                                                                           y=0,
                                                                                           type="switch",
                                                                                           id=0))
                    if created:
                        connected_device.id = connected_device.pk
                        connected_device.save()
                        send_updates = True
                        print "Created device ", connected_device
                    break

                if connected_device:
                    for port in inner_interface.get('port', []):
                        for port_id in port.get('id', []):
                            if port_id['type'] == 'ifname':
                                name = port_id['value']
                                break
                        connected_interface, created = Interface.objects.get_or_create(device_id=connected_device.pk,
                                                                                       name=name,
                                                                                       defaults=dict(id=0))
                        if created:
                            connected_interface.id = connected_interface.pk
                            connected_interface.save()
                            print "Created interface ", connected_interface
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
                        print "Created link ", link
                        send_updates = True

        if send_updates:
            send_snapshot(Group("topology-%s" % topology_id), topology_id)


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
    topology_id = parse_topology_id(data)
    topology, created = Topology.objects.get_or_create(
        topology_id=topology_id, defaults=dict(name="topology", scale=1.0, panX=0, panY=0))
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
                                        scale='scale'), topology.__dict__)

    message.reply_channel.send({"text": json.dumps(["Topology", topology_data])})
    send_snapshot(message.reply_channel, topology_id)
    send_history(message.reply_channel, topology_id)


def send_snapshot(channel, topology_id):
    interfaces = defaultdict(list)

    for i in (Interface.objects
              .filter(device__topology_id=topology_id)
              .values()):
        interfaces[i['device_id']].append(i)
    devices = list(Device.objects
                         .filter(topology_id=topology_id).values())
    for device in devices:
        device['interfaces'] = interfaces[device['device_id']]

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
    snapshot = dict(sender=0,
                    devices=devices,
                    links=links)
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
    Group("topology-%s" % message.channel_session['topology_id']).discard(message.reply_channel)


def console_printer(message):
    print message['text']  # pragma: no cover

# Worker channel events


@channel_session
def worker_connect(message):
    Group("workers").add(message.reply_channel)


@channel_session
def worker_message(message):
    # Channel('console_printer').send({"text": message['text']})
    pass


@channel_session
def worker_disconnect(message):
    pass


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
