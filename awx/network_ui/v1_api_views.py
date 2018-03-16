import channels
import json
from rest_framework import viewsets
from utils import transform_dict

from awx.network_ui.models import Device
from awx.network_ui.models import Link
from awx.network_ui.models import Topology
from awx.network_ui.models import Interface
from awx.network_ui.models import Group
from awx.network_ui.models import GroupDevice
from awx.network_ui.models import Stream
from awx.network_ui.models import Process
from awx.network_ui.models import Toolbox
from awx.network_ui.models import ToolboxItem
from awx.network_ui.models import TopologyInventory

from awx.network_ui.v1_api_serializers import DeviceSerializer
from awx.network_ui.v1_api_serializers import LinkSerializer
from awx.network_ui.v1_api_serializers import TopologySerializer
from awx.network_ui.v1_api_serializers import InterfaceSerializer
from awx.network_ui.v1_api_serializers import GroupSerializer
from awx.network_ui.v1_api_serializers import GroupDeviceSerializer
from awx.network_ui.v1_api_serializers import StreamSerializer
from awx.network_ui.v1_api_serializers import ProcessSerializer
from awx.network_ui.v1_api_serializers import ToolboxSerializer
from awx.network_ui.v1_api_serializers import ToolboxItemSerializer
from awx.network_ui.v1_api_serializers import TopologyInventorySerializer


class DeviceViewSet(viewsets.ModelViewSet):

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    def create(self, request, *args, **kwargs):
        response = super(DeviceViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['device_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "DeviceCreate"
        message['device_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Device.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in Device.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "DeviceUpdate"
        message['device_id'] = pk
        message['sender'] = 0

        for topology_id in Device.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(DeviceViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(DeviceViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(DeviceViewSet, self).destroy(request, pk, *args, **kwargs)


class LinkViewSet(viewsets.ModelViewSet):

    queryset = Link.objects.all()
    serializer_class = LinkSerializer

    def create(self, request, *args, **kwargs):
        response = super(LinkViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['link_id']
        message = dict()

        message.update(transform_dict({'to_device__id': 'to_device_id',
                                       'from_interface__id': 'from_interface_id',
                                       'name': 'name',
                                       'from_device__id': 'from_device_id',
                                       'id': 'id',
                                       'to_interface__id': 'to_interface_id',
                                       }, Link.objects.filter(pk=pk).values(*['to_device__id',
                                                                              'from_interface__id',
                                                                              'name',
                                                                              'from_device__id',
                                                                              'id',
                                                                              'to_interface__id',
                                                                              ])[0]))

        message['msg_type'] = "LinkCreate"
        message['link_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Link.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True)
        for topology_id in Link.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "LinkUpdate"
        message['link_id'] = pk
        message['sender'] = 0

        for topology_id in Link.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(LinkViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(LinkViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(LinkViewSet, self).destroy(request, pk, *args, **kwargs)


class TopologyViewSet(viewsets.ModelViewSet):

    queryset = Topology.objects.all()
    serializer_class = TopologySerializer

    def create(self, request, *args, **kwargs):
        response = super(TopologyViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['topology_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "TopologyCreate"
        message['topology_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Topology.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in Topology.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "TopologyUpdate"
        message['topology_id'] = pk
        message['sender'] = 0

        for topology_id in Topology.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(TopologyViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(TopologyViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(TopologyViewSet, self).destroy(request, pk, *args, **kwargs)


class InterfaceViewSet(viewsets.ModelViewSet):

    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer

    def create(self, request, *args, **kwargs):
        response = super(InterfaceViewSet, self).create(
            request, *args, **kwargs)
        print response.data
        pk = response.data['interface_id']
        message = dict()

        message.update(transform_dict({'id': 'id',
                                       'device__id': 'device_id',
                                       'name': 'name',
                                       }, Interface.objects.filter(pk=pk).values(*['id',
                                                                                   'device__id',
                                                                                   'name',
                                                                                   ])[0]))

        message['msg_type'] = "InterfaceCreate"
        message['interface_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Interface.objects.filter(pk=pk).values_list('device__topology_id', flat=True)
        for topology_id in Interface.objects.filter(pk=pk).values_list('device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "InterfaceUpdate"
        message['interface_id'] = pk
        message['sender'] = 0

        for topology_id in Interface.objects.filter(pk=pk).values_list('device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(InterfaceViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(InterfaceViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(InterfaceViewSet, self).destroy(request, pk, *args, **kwargs)


class GroupViewSet(viewsets.ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def create(self, request, *args, **kwargs):
        response = super(GroupViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['group_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "GroupCreate"
        message['group_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Group.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in Group.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "GroupUpdate"
        message['group_id'] = pk
        message['sender'] = 0

        for topology_id in Group.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(GroupViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(GroupViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(GroupViewSet, self).destroy(request, pk, *args, **kwargs)


class GroupDeviceViewSet(viewsets.ModelViewSet):

    queryset = GroupDevice.objects.all()
    serializer_class = GroupDeviceSerializer

    def create(self, request, *args, **kwargs):
        response = super(GroupDeviceViewSet, self).create(
            request, *args, **kwargs)
        print response.data
        pk = response.data['group_device_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "GroupDeviceCreate"
        message['group_device_id'] = pk
        message['sender'] = 0

        print "sending to topologies", GroupDevice.objects.filter(pk=pk).values_list('group__topology_id', flat=True)
        for topology_id in GroupDevice.objects.filter(pk=pk).values_list('group__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "GroupDeviceUpdate"
        message['group_device_id'] = pk
        message['sender'] = 0

        for topology_id in GroupDevice.objects.filter(pk=pk).values_list('group__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(GroupDeviceViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(GroupDeviceViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(GroupDeviceViewSet, self).destroy(request, pk, *args, **kwargs)


class StreamViewSet(viewsets.ModelViewSet):

    queryset = Stream.objects.all()
    serializer_class = StreamSerializer

    def create(self, request, *args, **kwargs):
        response = super(StreamViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['stream_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "StreamCreate"
        message['stream_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Stream.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True)
        for topology_id in Stream.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "StreamUpdate"
        message['stream_id'] = pk
        message['sender'] = 0

        for topology_id in Stream.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(StreamViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(StreamViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(StreamViewSet, self).destroy(request, pk, *args, **kwargs)


class ProcessViewSet(viewsets.ModelViewSet):

    queryset = Process.objects.all()
    serializer_class = ProcessSerializer

    def create(self, request, *args, **kwargs):
        response = super(ProcessViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['process_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "ProcessCreate"
        message['process_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Process.objects.filter(pk=pk).values_list('device__topology_id', flat=True)
        for topology_id in Process.objects.filter(pk=pk).values_list('device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "ProcessUpdate"
        message['process_id'] = pk
        message['sender'] = 0

        for topology_id in Process.objects.filter(pk=pk).values_list('device__topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(ProcessViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(ProcessViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(ProcessViewSet, self).destroy(request, pk, *args, **kwargs)


class ToolboxViewSet(viewsets.ModelViewSet):

    queryset = Toolbox.objects.all()
    serializer_class = ToolboxSerializer

    def create(self, request, *args, **kwargs):
        response = super(ToolboxViewSet, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['toolbox_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "ToolboxCreate"
        message['toolbox_id'] = pk
        message['sender'] = 0

        print "sending to all topologies"
        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "ToolboxUpdate"
        message['toolbox_id'] = pk
        message['sender'] = 0

        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(ToolboxViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(ToolboxViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(ToolboxViewSet, self).destroy(request, pk, *args, **kwargs)


class ToolboxItemViewSet(viewsets.ModelViewSet):

    queryset = ToolboxItem.objects.all()
    serializer_class = ToolboxItemSerializer

    def create(self, request, *args, **kwargs):
        response = super(ToolboxItemViewSet, self).create(
            request, *args, **kwargs)
        print response.data
        pk = response.data['toolbox_item_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "ToolboxItemCreate"
        message['toolbox_item_id'] = pk
        message['sender'] = 0

        print "sending to all topologies"
        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "ToolboxItemUpdate"
        message['toolbox_item_id'] = pk
        message['sender'] = 0

        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(ToolboxItemViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(ToolboxItemViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(ToolboxItemViewSet, self).destroy(request, pk, *args, **kwargs)


class TopologyInventoryViewSet(viewsets.ModelViewSet):

    queryset = TopologyInventory.objects.all()
    serializer_class = TopologyInventorySerializer

    def create(self, request, *args, **kwargs):
        response = super(TopologyInventoryViewSet, self).create(
            request, *args, **kwargs)
        print response.data
        pk = response.data['topology_inventory_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "TopologyInventoryCreate"
        message['topology_inventory_id'] = pk
        message['sender'] = 0

        print "sending to topologies", TopologyInventory.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in TopologyInventory.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "TopologyInventoryUpdate"
        message['topology_inventory_id'] = pk
        message['sender'] = 0

        for topology_id in TopologyInventory.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group(
                "topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(TopologyInventoryViewSet, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(TopologyInventoryViewSet, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(TopologyInventoryViewSet, self).destroy(request, pk, *args, **kwargs)
