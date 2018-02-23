import json
import channels
from utils import transform_dict

from awx.api.generics import ListCreateAPIView
from awx.api.generics import RetrieveUpdateDestroyAPIView
from awx.network_ui.models import (Device,
                                   Link,
                                   Topology,
                                   Interface,
                                   Group,
                                   GroupDevice,
                                   Stream,
                                   Process,
                                   Toolbox,
                                   ToolboxItem,
                                   TopologyInventory,
                                   )
from awx.network_ui.v2_api_serializers import (DeviceSerializer,
                                               LinkSerializer,
                                               TopologySerializer,
                                               InterfaceSerializer,
                                               GroupSerializer,
                                               GroupDeviceSerializer,
                                               StreamSerializer,
                                               ProcessSerializer,
                                               ToolboxSerializer,
                                               ToolboxItemSerializer,
                                               TopologyInventorySerializer,
                                               )


class DeviceList(ListCreateAPIView):

    model = Device
    serializer_class = DeviceSerializer

    def create(self, request, *args, **kwargs):
        response = super(DeviceList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['device_id']
        message = dict()

        message.update(transform_dict({'interface_id_seq': 'interface_id_seq',
                                       'name': 'name',
                                       'process_id_seq': 'process_id_seq',
                                       'device_type': 'type',
                                       'host_id': 'host_id',
                                       'y': 'y',
                                       'x': 'x',
                                       'topology_id': 'topology_id',
                                       'id': 'id',
                                       }, Device.objects.filter(pk=pk).values(*['interface_id_seq',
                                                                                'name',
                                                                                'process_id_seq',
                                                                                'device_type',
                                                                                'host_id',
                                                                                'y',
                                                                                'x',
                                                                                'topology_id',
                                                                                'id',
                                                                                ])[0]))

        message['msg_type'] = "DeviceCreate"
        message['device_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Device.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in Device.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class DeviceDetail(RetrieveUpdateDestroyAPIView):

    model = Device
    serializer_class = DeviceSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "DeviceUpdate"
        message['device_id'] = pk
        message['sender'] = 0

        for topology_id in Device.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(DeviceDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(DeviceDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(DeviceDetail, self).destroy(request, pk, *args, **kwargs)


class LinkList(ListCreateAPIView):

    model = Link
    serializer_class = LinkSerializer

    def create(self, request, *args, **kwargs):
        response = super(LinkList, self).create(request, *args, **kwargs)
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

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class LinkDetail(RetrieveUpdateDestroyAPIView):

    model = Link
    serializer_class = LinkSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "LinkUpdate"
        message['link_id'] = pk
        message['sender'] = 0

        for topology_id in Link.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(LinkDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(LinkDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(LinkDetail, self).destroy(request, pk, *args, **kwargs)


class TopologyList(ListCreateAPIView):

    model = Topology
    serializer_class = TopologySerializer

    def create(self, request, *args, **kwargs):
        response = super(TopologyList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['topology_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "TopologyCreate"
        message['topology_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Topology.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in Topology.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class TopologyDetail(RetrieveUpdateDestroyAPIView):

    model = Topology
    serializer_class = TopologySerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "TopologyUpdate"
        message['topology_id'] = pk
        message['sender'] = 0

        for topology_id in Topology.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(TopologyDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(TopologyDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(TopologyDetail, self).destroy(request, pk, *args, **kwargs)


class InterfaceList(ListCreateAPIView):

    model = Interface
    serializer_class = InterfaceSerializer

    def create(self, request, *args, **kwargs):
        response = super(InterfaceList, self).create(request, *args, **kwargs)
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

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class InterfaceDetail(RetrieveUpdateDestroyAPIView):

    model = Interface
    serializer_class = InterfaceSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "InterfaceUpdate"
        message['interface_id'] = pk
        message['sender'] = 0

        for topology_id in Interface.objects.filter(pk=pk).values_list('device__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(InterfaceDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(InterfaceDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(InterfaceDetail, self).destroy(request, pk, *args, **kwargs)


class GroupList(ListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer

    def create(self, request, *args, **kwargs):
        response = super(GroupList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['group_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "GroupCreate"
        message['group_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Group.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in Group.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class GroupDetail(RetrieveUpdateDestroyAPIView):

    model = Group
    serializer_class = GroupSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "GroupUpdate"
        message['group_id'] = pk
        message['sender'] = 0

        for topology_id in Group.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(GroupDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(GroupDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(GroupDetail, self).destroy(request, pk, *args, **kwargs)


class GroupDeviceList(ListCreateAPIView):

    model = GroupDevice
    serializer_class = GroupDeviceSerializer

    def create(self, request, *args, **kwargs):
        response = super(GroupDeviceList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['group_device_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "GroupDeviceCreate"
        message['group_device_id'] = pk
        message['sender'] = 0

        print "sending to topologies", GroupDevice.objects.filter(pk=pk).values_list('group__topology_id', flat=True)
        for topology_id in GroupDevice.objects.filter(pk=pk).values_list('group__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class GroupDeviceDetail(RetrieveUpdateDestroyAPIView):

    model = GroupDevice
    serializer_class = GroupDeviceSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "GroupDeviceUpdate"
        message['group_device_id'] = pk
        message['sender'] = 0

        for topology_id in GroupDevice.objects.filter(pk=pk).values_list('group__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(GroupDeviceDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(GroupDeviceDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(GroupDeviceDetail, self).destroy(request, pk, *args, **kwargs)


class StreamList(ListCreateAPIView):

    model = Stream
    serializer_class = StreamSerializer

    def create(self, request, *args, **kwargs):
        response = super(StreamList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['stream_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "StreamCreate"
        message['stream_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Stream.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True)
        for topology_id in Stream.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class StreamDetail(RetrieveUpdateDestroyAPIView):

    model = Stream
    serializer_class = StreamSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "StreamUpdate"
        message['stream_id'] = pk
        message['sender'] = 0

        for topology_id in Stream.objects.filter(pk=pk).values_list('from_device__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(StreamDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(StreamDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(StreamDetail, self).destroy(request, pk, *args, **kwargs)


class ProcessList(ListCreateAPIView):

    model = Process
    serializer_class = ProcessSerializer

    def create(self, request, *args, **kwargs):
        response = super(ProcessList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['process_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "ProcessCreate"
        message['process_id'] = pk
        message['sender'] = 0

        print "sending to topologies", Process.objects.filter(pk=pk).values_list('device__topology_id', flat=True)
        for topology_id in Process.objects.filter(pk=pk).values_list('device__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class ProcessDetail(RetrieveUpdateDestroyAPIView):

    model = Process
    serializer_class = ProcessSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "ProcessUpdate"
        message['process_id'] = pk
        message['sender'] = 0

        for topology_id in Process.objects.filter(pk=pk).values_list('device__topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(ProcessDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(ProcessDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(ProcessDetail, self).destroy(request, pk, *args, **kwargs)


class ToolboxList(ListCreateAPIView):

    model = Toolbox
    serializer_class = ToolboxSerializer

    def create(self, request, *args, **kwargs):
        response = super(ToolboxList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['toolbox_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "ToolboxCreate"
        message['toolbox_id'] = pk
        message['sender'] = 0

        print "sending to all topologies"
        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class ToolboxDetail(RetrieveUpdateDestroyAPIView):

    model = Toolbox
    serializer_class = ToolboxSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "ToolboxUpdate"
        message['toolbox_id'] = pk
        message['sender'] = 0

        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(ToolboxDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(ToolboxDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(ToolboxDetail, self).destroy(request, pk, *args, **kwargs)


class ToolboxItemList(ListCreateAPIView):

    model = ToolboxItem
    serializer_class = ToolboxItemSerializer

    def create(self, request, *args, **kwargs):
        response = super(ToolboxItemList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['toolbox_item_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "ToolboxItemCreate"
        message['toolbox_item_id'] = pk
        message['sender'] = 0

        print "sending to all topologies"
        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class ToolboxItemDetail(RetrieveUpdateDestroyAPIView):

    model = ToolboxItem
    serializer_class = ToolboxItemSerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "ToolboxItemUpdate"
        message['toolbox_item_id'] = pk
        message['sender'] = 0

        for topology_id in Topology.objects.all().values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(ToolboxItemDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(ToolboxItemDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(ToolboxItemDetail, self).destroy(request, pk, *args, **kwargs)


class TopologyInventoryList(ListCreateAPIView):

    model = TopologyInventory
    serializer_class = TopologyInventorySerializer

    def create(self, request, *args, **kwargs):
        response = super(TopologyInventoryList, self).create(request, *args, **kwargs)
        print response.data
        pk = response.data['topology_inventory_id']
        message = dict()

        message.update(response.data)

        message['msg_type'] = "TopologyInventoryCreate"
        message['topology_inventory_id'] = pk
        message['sender'] = 0

        print "sending to topologies", TopologyInventory.objects.filter(pk=pk).values_list('topology_id', flat=True)
        for topology_id in TopologyInventory.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})
            print "Sent message", message
        return response


class TopologyInventoryDetail(RetrieveUpdateDestroyAPIView):

    model = TopologyInventory
    serializer_class = TopologyInventorySerializer

    def update(self, request, pk=None, *args, **kwargs):
        message = dict()
        message.update(json.loads(request.body))
        message['msg_type'] = "TopologyInventoryUpdate"
        message['topology_inventory_id'] = pk
        message['sender'] = 0

        for topology_id in TopologyInventory.objects.filter(pk=pk).values_list('topology_id', flat=True):

            channels.Group("topology-%s" % topology_id).send({"text": json.dumps([message['msg_type'], message])})

        return super(TopologyInventoryDetail, self).update(request, pk, *args, **kwargs)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return super(TopologyInventoryDetail, self).partial_update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        return super(TopologyInventoryDetail, self).destroy(request, pk, *args, **kwargs)
