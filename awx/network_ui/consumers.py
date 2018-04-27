# Copyright (c) 2017 Red Hat, Inc
from channels import Group
from channels.sessions import channel_session
from awx.network_ui.models import Topology, Device, Link, Client, Interface
from awx.network_ui.models import TopologyInventory
import urlparse
from django.db.models import Q
from collections import defaultdict
import logging


from awx.network_ui.utils import transform_dict

import json

logger = logging.getLogger("awx.network_ui.consumers")


def parse_inventory_id(data):
    inventory_id = data.get('inventory_id', ['null'])
    try:
        inventory_id = int(inventory_id[0])
    except ValueError:
        inventory_id = None
    if not inventory_id:
        inventory_id = None
    return inventory_id


class NetworkingEvents(object):

    '''
    Provides handlers for the networking events for the topology canvas.
    '''

    def parse_message_text(self, message_text, client_id):
        '''
        See the Messages of CONTRIBUTING.md for the message format.
        '''
        data = json.loads(message_text)
        if len(data) == 2:
            message_type = data.pop(0)
            message_value = data.pop(0)
            if isinstance(message_value, list):
                logger.error("Message has no sender")
                return None, None
            if isinstance(message_value, dict) and client_id != message_value.get('sender'):
                logger.error("client_id mismatch expected: %s actual %s", client_id, message_value.get('sender'))
                return None, None
            return message_type, message_value
        else:
            logger.error("Invalid message text")
            return None, None

    def handle(self, message):
        '''
        Dispatches a message based on the message type to a handler function
        of name onX where X is the message type.
        '''
        topology_id = message.get('topology')
        assert topology_id is not None, "No topology_id"
        client_id = message.get('client')
        assert client_id is not None, "No client_id"
        message_type, message_value = self.parse_message_text(message['text'], client_id)
        if message_type is None:
            return
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
                                     type='device_type',
                                     id='cid',
                                     host_id='host_id'), device)
        logger.info("Device created %s", device)
        d, _ = Device.objects.get_or_create(topology_id=topology_id, cid=device['cid'], defaults=device)
        d.x = device['x']
        d.y = device['y']
        d.device_type = device['device_type']
        d.host_id = device['host_id']
        d.save()
        (Topology.objects
                 .filter(pk=topology_id, device_id_seq__lt=device['cid'])
                 .update(device_id_seq=device['cid']))

    def onDeviceDestroy(self, device, topology_id, client_id):
        logger.info("Device removed %s", device)
        Device.objects.filter(topology_id=topology_id, cid=device['id']).delete()

    def onDeviceMove(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, cid=device['id']).update(x=device['x'], y=device['y'])

    def onDeviceInventoryUpdate(self, device, topology_id, client_id):
        Device.objects.filter(topology_id=topology_id, cid=device['id']).update(host_id=device['host_id'])

    def onDeviceLabelEdit(self, device, topology_id, client_id):
        logger.debug("Device label edited %s", device)
        Device.objects.filter(topology_id=topology_id, cid=device['id']).update(name=device['name'])

    def onInterfaceLabelEdit(self, interface, topology_id, client_id):
        (Interface.objects
                  .filter(device__topology_id=topology_id,
                          cid=interface['id'],
                          device__cid=interface['device_id'])
                  .update(name=interface['name']))

    def onLinkLabelEdit(self, link, topology_id, client_id):
        logger.debug("Link label edited %s", link)
        Link.objects.filter(from_device__topology_id=topology_id, cid=link['id']).update(name=link['name'])

    def onInterfaceCreate(self, interface, topology_id, client_id):
        Interface.objects.get_or_create(device_id=Device.objects.get(cid=interface['device_id'],
                                                                     topology_id=topology_id).pk,
                                        cid=interface['id'],
                                        defaults=dict(name=interface['name']))
        (Device.objects
               .filter(cid=interface['device_id'],
                       topology_id=topology_id,
                       interface_id_seq__lt=interface['id'])
               .update(interface_id_seq=interface['id']))

    def onLinkCreate(self, link, topology_id, client_id):
        logger.debug("Link created %s", link)
        device_map = dict(Device.objects
                                .filter(topology_id=topology_id, cid__in=[link['from_device_id'], link['to_device_id']])
                                .values_list('cid', 'pk'))
        Link.objects.get_or_create(cid=link['id'],
                                   name=link['name'],
                                   from_device_id=device_map[link['from_device_id']],
                                   to_device_id=device_map[link['to_device_id']],
                                   from_interface_id=Interface.objects.get(device_id=device_map[link['from_device_id']],
                                                                           cid=link['from_interface_id']).pk,
                                   to_interface_id=Interface.objects.get(device_id=device_map[link['to_device_id']],
                                                                         cid=link['to_interface_id']).pk)
        (Topology.objects
                 .filter(pk=topology_id, link_id_seq__lt=link['id'])
                 .update(link_id_seq=link['id']))

    def onLinkDestroy(self, link, topology_id, client_id):
        logger.debug("Link deleted %s", link)
        device_map = dict(Device.objects
                                .filter(topology_id=topology_id, cid__in=[link['from_device_id'], link['to_device_id']])
                                .values_list('cid', 'pk'))
        if link['from_device_id'] not in device_map:
            return
        if link['to_device_id'] not in device_map:
            return
        Link.objects.filter(cid=link['id'],
                            from_device_id=device_map[link['from_device_id']],
                            to_device_id=device_map[link['to_device_id']],
                            from_interface_id=Interface.objects.get(device_id=device_map[link['from_device_id']],
                                                                    cid=link['from_interface_id']).pk,
                            to_interface_id=Interface.objects.get(device_id=device_map[link['to_device_id']],
                                                                  cid=link['to_interface_id']).pk).delete()

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


networking_events_dispatcher = NetworkingEvents()


@channel_session
def ws_connect(message):
    data = urlparse.parse_qs(message.content['query_string'])
    inventory_id = parse_inventory_id(data)
    topology_ids = list(TopologyInventory.objects.filter(inventory_id=inventory_id).values_list('pk', flat=True))
    topology_id = None
    if len(topology_ids) > 0:
        topology_id = topology_ids[0]
    if topology_id is not None:
        topology = Topology.objects.get(pk=topology_id)
    else:
        topology = Topology(name="topology", scale=1.0, panX=0, panY=0)
        topology.save()
        TopologyInventory(inventory_id=inventory_id, topology_id=topology.pk).save()
    topology_id = topology.pk
    message.channel_session['topology_id'] = topology_id
    Group("topology-%s" % topology_id).add(message.reply_channel)
    client = Client()
    client.save()
    message.channel_session['client_id'] = client.pk
    Group("client-%s" % client.pk).add(message.reply_channel)
    message.reply_channel.send({"text": json.dumps(["id", client.pk])})
    message.reply_channel.send({"text": json.dumps(["topology_id", topology_id])})
    topology_data = transform_dict(dict(id='topology_id',
                                        name='name',
                                        panX='panX',
                                        panY='panY',
                                        scale='scale',
                                        link_id_seq='link_id_seq',
                                        device_id_seq='device_id_seq'), topology.__dict__)

    message.reply_channel.send({"text": json.dumps(["Topology", topology_data])})
    send_snapshot(message.reply_channel, topology_id)


def send_snapshot(channel, topology_id):
    interfaces = defaultdict(list)

    for i in (Interface.objects
              .filter(device__topology_id=topology_id)
              .values()):
        i = transform_dict(dict(cid='id',
                                device_id='device_id',
                                id='interface_id',
                                name='name'), i)
        interfaces[i['device_id']].append(i)
    devices = list(Device.objects.filter(topology_id=topology_id).values())
    devices = [transform_dict(dict(cid='id',
                                   id='device_id',
                                   device_type='device_type',
                                   host_id='host_id',
                                   name='name',
                                   x='x',
                                   y='y',
                                   interface_id_seq='interface_id_seq'), x) for x in devices]
    for device in devices:
        device['interfaces'] = interfaces[device['device_id']]

    links = [dict(id=x['cid'],
                  name=x['name'],
                  from_device_id=x['from_device__cid'],
                  to_device_id=x['to_device__cid'],
                  from_interface_id=x['from_interface__cid'],
                  to_interface_id=x['to_interface__cid'])
             for x in list(Link.objects
                               .filter(Q(from_device__topology_id=topology_id) |
                                       Q(to_device__topology_id=topology_id))
                               .values('cid',
                                       'name',
                                       'from_device__cid',
                                       'to_device__cid',
                                       'from_interface__cid',
                                       'to_interface__cid'))]
    snapshot = dict(sender=0,
                    devices=devices,
                    links=links)
    channel.send({"text": json.dumps(["Snapshot", snapshot])})


@channel_session
def ws_message(message):
    # Send to all clients editing the topology
    Group("topology-%s" % message.channel_session['topology_id']).send({"text": message['text']})
    # Send to networking_events handler
    networking_events_dispatcher.handle({"text": message['text'],
                                         "topology": message.channel_session['topology_id'],
                                         "client": message.channel_session['client_id']})


@channel_session
def ws_disconnect(message):
    if 'topology_id' in message.channel_session:
        Group("topology-%s" % message.channel_session['topology_id']).discard(message.reply_channel)

