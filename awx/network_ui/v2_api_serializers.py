from rest_framework import serializers

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


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('device_id', 'topology', 'name', 'x', 'y', 'id', 'type', 'interface_id_seq', 'process_id_seq', 'host_id',)


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('link_id', 'from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)


class TopologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Topology
        fields = ('topology_id', 'name', 'scale', 'panX', 'panY', 'device_id_seq', 'link_id_seq', 'group_id_seq', 'stream_id_seq',)


class InterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interface
        fields = ('interface_id', 'device', 'name', 'id',)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('group_id', 'id', 'name', 'x1', 'y1', 'x2', 'y2', 'topology', 'type',)


class GroupDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDevice
        fields = ('group_device_id', 'group', 'device',)


class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = ('stream_id', 'from_device', 'to_device', 'label', 'id',)


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ('process_id', 'device', 'name', 'type', 'id',)


class ToolboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Toolbox
        fields = ('toolbox_id', 'name',)


class ToolboxItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolboxItem
        fields = ('toolbox_item_id', 'toolbox', 'data',)


class TopologyInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TopologyInventory
        fields = ('topology_inventory_id', 'topology', 'inventory_id',)
