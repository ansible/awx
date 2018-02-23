# Copyright (c) 2017 Red Hat, Inc

from awx.network_ui.models import Topology, Device, Link, Interface, Group, GroupDevice, Process, Stream
from django.db.models import Q
import yaml
import json
from collections import defaultdict

NetworkAnnotatedInterface = Interface.objects.values('name',
                                                     'id',
                                                     'from_link__pk',
                                                     'to_link__pk',
                                                     'from_link__to_device__name',
                                                     'to_link__from_device__name',
                                                     'from_link__to_interface__name',
                                                     'to_link__from_interface__name')


def topology_data(topology_id):

        data = dict(devices=[],
                    links=[],
                    groups=[],
                    streams=[])

        topology = Topology.objects.get(pk=topology_id)

        data['name'] = topology.name
        data['topology_id'] = topology_id

        groups = list(Group.objects.filter(topology_id=topology_id).values())
        group_devices = GroupDevice.objects.filter(group__topology_id=topology_id).values('group_id', 'device_id', 'device__name', 'group__name')
        group_device_map = defaultdict(list)

        for group_device in group_devices:
            group_device_map[group_device['group_id']].append(group_device)

        device_group_map = defaultdict(list)
        for group_device in group_devices:
            device_group_map[group_device['device_id']].append(group_device)

        for group in groups:
            group['members'] = [x['device__name'] for x in group_device_map[group['group_id']]]
        data['groups'] = groups

        links = list(Link.objects
                         .filter(Q(from_device__topology_id=topology_id) |
                                 Q(to_device__topology_id=topology_id)))

        interfaces = Interface.objects.filter(device__topology_id=topology_id)
        processes = Process.objects.filter(device__topology_id=topology_id)

        for device in Device.objects.filter(topology_id=topology_id).order_by('name'):
            interfaces = list(NetworkAnnotatedInterface.filter(device_id=device.pk).order_by('name'))
            interfaces = [dict(name=x['name'],
                               network=x['from_link__pk'] or x['to_link__pk'],
                               remote_device_name=x['from_link__to_device__name'] or x['to_link__from_device__name'],
                               remote_interface_name=x['from_link__to_interface__name'] or x['to_link__from_interface__name'],
                               id=x['id'],
                               ) for x in interfaces]
            processes = list(Process.objects.filter(device_id=device.pk).values())
            data['devices'].append(dict(name=device.name,
                                        type=device.device_type,
                                        x=device.x,
                                        y=device.y,
                                        id=device.id,
                                        interfaces=interfaces,
                                        processes=processes,
                                        groups=[x['group__name'] for x in device_group_map[device.device_id]]))

        for link in links:
            data['links'].append(dict(from_device=link.from_device.name,
                                      to_device=link.to_device.name,
                                      from_interface=link.from_interface.name,
                                      to_interface=link.to_interface.name,
                                      from_device_id=link.from_device.id,
                                      to_device_id=link.to_device.id,
                                      from_interface_id=link.from_interface.id,
                                      to_interface_id=link.to_interface.id,
                                      name=link.name,
                                      network=link.pk))

        streams = list(Stream.objects
                       .filter(Q(from_device__topology_id=topology_id) |
                               Q(to_device__topology_id=topology_id)))

        for stream in streams:
            data['streams'].append(dict(from_id=stream.from_device.id,
                                        to_id=stream.to_device.id,
                                        from_device=stream.from_device.name,
                                        to_device=stream.to_device.name,
                                        label=stream.label,
                                        id=stream.id))

        return data


def yaml_serialize_topology(topology_id):
    return yaml.safe_dump(topology_data(topology_id), default_flow_style=False)


def json_serialize_topology(topology_id):
    return json.dumps(topology_data(topology_id))
