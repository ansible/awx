# Copyright (c) 2017 Red Hat, Inc
# In consumers.py
from channels import Group, Channel
from channels.sessions import channel_session
from awx.network_ui.models import Topology, Device, Link, Client, TopologyHistory, MessageType, Interface
from awx.network_ui.models import Group as DeviceGroup
from awx.network_ui.models import GroupDevice as GroupDeviceMap
from awx.network_ui.models import Process, Stream
from awx.network_ui.models import Toolbox, ToolboxItem
from awx.network_ui.models import FSMTrace, EventTrace, Coverage, TopologySnapshot
from awx.network_ui.models import TopologyInventory
from awx.network_ui.models import TestCase, TestResult, CodeUnderTest, Result
import urlparse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from collections import defaultdict
import logging
from django.utils.dateparse import parse_datetime


from awx.network_ui.utils import transform_dict
from pprint import pformat

import json
# Connected to websocket.connect

HISTORY_MESSAGE_IGNORE_TYPES = ['DeviceSelected',
                                'DeviceUnSelected',
                                'LinkSelected',
                                'LinkUnSelected',
                                'MouseEvent',
                                'MouseWheelEvent',
                                'KeyEvent']


logger = logging.getLogger("awx.network_ui.consumers")


class NetworkUIException(Exception):

    pass


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
            logger.error("Message has no sender")
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
            try:
                handler(message_value, topology_id, client_id)
            except NetworkUIException, e:
                Group("client-%s" % client_id).send({"text": json.dumps(["Error", str(e)])})
                raise
            except Exception, e:
                Group("client-%s" % client_id).send({"text": json.dumps(["Error", "Server Error"])})
                raise
            except BaseException, e:
                Group("client-%s" % client_id).send({"text": json.dumps(["Error", "Server Error"])})
                raise
        else:
            logger.warning("Unsupported message %s: no handler", message_type)

    def get_handler(self, message_type):
        return getattr(self, "on{0}".format(message_type), None)

    def onDeviceCreate(self, device, topology_id, client_id):
        device = transform_dict(dict(x='x',
                                     y='y',
                                     name='name',
                                     type='device_type',
                                     id='id',
                                     host_id='host_id'), device)
        logger.info("Device %s", device)
        d, _ = Device.objects.get_or_create(topology_id=topology_id, id=device['id'], defaults=device)
        d.x = device['x']
        d.y = device['y']
        d.device_type = device['device_type']
        d.host_id = device['host_id']
        d.save()
        (Topology.objects
                 .filter(topology_id=topology_id, device_id_seq__lt=device['id'])
                 .update(device_id_seq=device['id']))

    def onDeviceDestroy(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).delete()

    def onDeviceMove(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).update(x=device['x'], y=device['y'])

    def onDeviceInventoryUpdate(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, id=device['id']).update(host_id=device['host_id'])

    def onGroupInventoryUpdate(self, group, topology_id, client_id):
        DeviceGroup.objects.filter(topology_id=topology_id, id=group['id']).update(inventory_group_id=group['group_id'])

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
                                      defaults=dict(name=process['name'], process_type=process['type']))
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

    def onMultipleMessage(self, message_value, topology_id, client_id):
        for message in message_value['messages']:
            handler = self.get_handler(message['msg_type'])
            if handler is not None:
                handler(message, topology_id, client_id)
            else:
                logger.warning("Unsupported message %s", message['msg_type'])

    def onCoverageRequest(self, coverage, topology_id, client_id):
        pass

    def onTestResult(self, test_result, topology_id, client_id):
        xyz, _, rest = test_result['code_under_test'].partition('-')
        commits_since, _, commit_hash = rest.partition('-')
        commit_hash = commit_hash.strip('g')

        x, y, z = [int(i) for i in xyz.split('.')]

        code_under_test, _ = CodeUnderTest.objects.get_or_create(version_x=x,
                                                                 version_y=y,
                                                                 version_z=z,
                                                                 commits_since=int(commits_since),
                                                                 commit_hash=commit_hash)

        tr = TestResult(id=test_result['id'],
                        result_id=Result.objects.get(name=test_result['result']).pk,
                        test_case_id=TestCase.objects.get(name=test_result['name']).pk,
                        code_under_test_id=code_under_test.pk,
                        client_id=client_id,
                        time=parse_datetime(test_result['date']))
        tr.save()


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
                                    type='group_type',
                                    group_id='inventory_group_id'), group)
        d, _ = DeviceGroup.objects.get_or_create(topology_id=topology_id, id=group['id'], defaults=group)
        d.x1 = group['x1']
        d.y1 = group['y1']
        d.x2 = group['x2']
        d.y2 = group['y2']
        d.group_type = group['group_type']
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


# UI Channel Events

@channel_session
def ws_connect(message):
    # Accept connection
    data = urlparse.parse_qs(message.content['query_string'])
    inventory_id = parse_inventory_id(data)
    topology_ids = list(TopologyInventory.objects.filter(inventory_id=inventory_id).values_list('topology_id', flat=True))
    topology_id = 0
    if len(topology_ids) > 0:
        topology_id = topology_ids[0]
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
    Group("client-%s" % client.pk).add(message.reply_channel)
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

