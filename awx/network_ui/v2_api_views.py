from rest_framework import viewsets

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

from awx.network_ui.v2_api_serializers import DeviceSerializer
from awx.network_ui.v2_api_serializers import LinkSerializer
from awx.network_ui.v2_api_serializers import TopologySerializer
from awx.network_ui.v2_api_serializers import InterfaceSerializer
from awx.network_ui.v2_api_serializers import GroupSerializer
from awx.network_ui.v2_api_serializers import GroupDeviceSerializer
from awx.network_ui.v2_api_serializers import StreamSerializer
from awx.network_ui.v2_api_serializers import ProcessSerializer
from awx.network_ui.v2_api_serializers import ToolboxSerializer
from awx.network_ui.v2_api_serializers import ToolboxItemSerializer
from awx.network_ui.v2_api_serializers import TopologyInventorySerializer


class DeviceViewSet(viewsets.ModelViewSet):

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    lookup_field = 'host_id'

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(DeviceViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(DeviceViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(DeviceViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(DeviceViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(DeviceViewSet, self).destroy(request, *args, **kwargs)
        return response


class LinkViewSet(viewsets.ModelViewSet):

    queryset = Link.objects.all()
    serializer_class = LinkSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(LinkViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(LinkViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(LinkViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(LinkViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(LinkViewSet, self).destroy(request, *args, **kwargs)
        return response


class TopologyViewSet(viewsets.ModelViewSet):

    queryset = Topology.objects.all()
    serializer_class = TopologySerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyViewSet, self).destroy(request, *args, **kwargs)
        return response


class InterfaceViewSet(viewsets.ModelViewSet):

    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(InterfaceViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(InterfaceViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(InterfaceViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(InterfaceViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(InterfaceViewSet, self).destroy(request, *args, **kwargs)
        return response


class GroupViewSet(viewsets.ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupViewSet, self).destroy(request, *args, **kwargs)
        return response


class GroupDeviceViewSet(viewsets.ModelViewSet):

    queryset = GroupDevice.objects.all()
    serializer_class = GroupDeviceSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupDeviceViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupDeviceViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupDeviceViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupDeviceViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(GroupDeviceViewSet, self).destroy(request, *args, **kwargs)
        return response


class StreamViewSet(viewsets.ModelViewSet):

    queryset = Stream.objects.all()
    serializer_class = StreamSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(StreamViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(StreamViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(StreamViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(StreamViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(StreamViewSet, self).destroy(request, *args, **kwargs)
        return response


class ProcessViewSet(viewsets.ModelViewSet):

    queryset = Process.objects.all()
    serializer_class = ProcessSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ProcessViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ProcessViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ProcessViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ProcessViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ProcessViewSet, self).destroy(request, *args, **kwargs)
        return response


class ToolboxViewSet(viewsets.ModelViewSet):

    queryset = Toolbox.objects.all()
    serializer_class = ToolboxSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxViewSet, self).destroy(request, *args, **kwargs)
        return response


class ToolboxItemViewSet(viewsets.ModelViewSet):

    queryset = ToolboxItem.objects.all()
    serializer_class = ToolboxItemSerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxItemViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxItemViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxItemViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxItemViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(ToolboxItemViewSet, self).destroy(request, *args, **kwargs)
        return response


class TopologyInventoryViewSet(viewsets.ModelViewSet):

    queryset = TopologyInventory.objects.all()
    serializer_class = TopologyInventorySerializer

    def retrieve(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyInventoryViewSet, self).retrieve(request, *args, **kwargs)
        return response

    def list(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyInventoryViewSet, self).list(request, *args, **kwargs)
        return response

    def update(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyInventoryViewSet, self).update(request, *args, **kwargs)
        return response

    def create(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyInventoryViewSet, self).create(request, *args, **kwargs)
        return response

    def destroy(self, request, *args, **kwargs):
        print (args, kwargs)
        response = super(TopologyInventoryViewSet, self).destroy(request, *args, **kwargs)
        return response
