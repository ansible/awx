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

from awx.network_ui.models import DataBinding

from awx.network_ui.models import DataType

from awx.network_ui.models import DataSheet

from awx.network_ui.models import Stream

from awx.network_ui.models import Process


class DeviceAdmin(admin.ModelAdmin):
    fields = ('topology', 'name', 'x', 'y', 'id', 'type', 'interface_id_seq', 'process_id_seq',)
    raw_id_fields = ('topology',)


admin.site.register(Device, DeviceAdmin)


class LinkAdmin(admin.ModelAdmin):
    fields = ('from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)
    raw_id_fields = ('from_device', 'to_device', 'from_interface', 'to_interface',)


admin.site.register(Link, LinkAdmin)


class TopologyAdmin(admin.ModelAdmin):
    fields = ('name', 'scale', 'panX', 'panY', 'device_id_seq', 'link_id_seq', 'group_id_seq', 'stream_id_seq',)
    raw_id_fields = ('group_id_seq',)


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
    fields = ('id', 'name', 'x1', 'y1', 'x2', 'y2', 'topology', 'type',)
    raw_id_fields = ('topology',)


admin.site.register(Group, GroupAdmin)


class GroupDeviceAdmin(admin.ModelAdmin):
    fields = ('group', 'device',)
    raw_id_fields = ('group', 'device',)


admin.site.register(GroupDevice, GroupDeviceAdmin)


class DataBindingAdmin(admin.ModelAdmin):
    fields = ('column', 'row', 'table', 'primary_key_id', 'field', 'data_type', 'sheet',)
    raw_id_fields = ('data_type', 'sheet',)


admin.site.register(DataBinding, DataBindingAdmin)


class DataTypeAdmin(admin.ModelAdmin):
    fields = ('type_name',)
    raw_id_fields = ()


admin.site.register(DataType, DataTypeAdmin)


class DataSheetAdmin(admin.ModelAdmin):
    fields = ('name', 'topology', 'client',)
    raw_id_fields = ('topology', 'client',)


admin.site.register(DataSheet, DataSheetAdmin)


class StreamAdmin(admin.ModelAdmin):
    fields = ('from_device', 'to_device', 'label', 'id',)
    raw_id_fields = ('stream_id', 'from_device', 'to_device',)


admin.site.register(Stream, StreamAdmin)


class ProcessAdmin(admin.ModelAdmin):
    fields = ('device', 'name', 'type', 'id',)
    raw_id_fields = ('device',)


admin.site.register(Process, ProcessAdmin)
