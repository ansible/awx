from django.contrib import admin

from awx.network_ui.models import Device

from awx.network_ui.models import Link

from awx.network_ui.models import Topology

from awx.network_ui.models import Client

from awx.network_ui.models import TopologyHistory

from awx.network_ui.models import MessageType

from awx.network_ui.models import Interface

from awx.network_ui.models import Group

from awx.network_ui.models import GroupDevice


class DeviceAdmin(admin.ModelAdmin):
    fields = ('topology', 'name', 'x', 'y', 'id', 'type', 'interface_id_seq',)
    raw_id_fields = ('topology',)


admin.site.register(Device, DeviceAdmin)


class LinkAdmin(admin.ModelAdmin):
    fields = ('from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)
    raw_id_fields = ('from_device', 'to_device', 'from_interface', 'to_interface',)


admin.site.register(Link, LinkAdmin)


class TopologyAdmin(admin.ModelAdmin):
    fields = ('name', 'scale', 'panX', 'panY', 'device_id_seq', 'link_id_seq', 'group_id_seq',)
    raw_id_fields = ('device_id_seq',)


admin.site.register(Topology, TopologyAdmin)


class ClientAdmin(admin.ModelAdmin):
    fields = ()
    raw_id_fields = ()


admin.site.register(Client, ClientAdmin)


class TopologyHistoryAdmin(admin.ModelAdmin):
    fields = ('topology', 'client', 'message_type', 'message_id', 'message_data', 'undone',)
    raw_id_fields = ('topology', 'client', 'message_type',)


admin.site.register(TopologyHistory, TopologyHistoryAdmin)


class MessageTypeAdmin(admin.ModelAdmin):
    fields = ('name',)
    raw_id_fields = ()


admin.site.register(MessageType, MessageTypeAdmin)


class InterfaceAdmin(admin.ModelAdmin):
    fields = ('device', 'name', 'id',)
    raw_id_fields = ('device',)


admin.site.register(Interface, InterfaceAdmin)


class GroupAdmin(admin.ModelAdmin):
    fields = ('id', 'name', 'x1', 'y1', 'x2', 'y2', 'topology',)
    raw_id_fields = ('id', 'y1', 'x2', 'topology',)


admin.site.register(Group, GroupAdmin)


class GroupDeviceAdmin(admin.ModelAdmin):
    fields = ('group', 'device',)
    raw_id_fields = ('group', 'device',)


admin.site.register(GroupDevice, GroupDeviceAdmin)
