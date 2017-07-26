from django.contrib import admin

from prototype.models import Device

from prototype.models import Link

from prototype.models import Topology

from prototype.models import Client

from prototype.models import TopologyHistory

from prototype.models import MessageType

from prototype.models import Interface


class DeviceAdmin(admin.ModelAdmin):
    fields = ('topology', 'name', 'x', 'y', 'id', 'type',)
    raw_id_fields = ('topology',)


admin.site.register(Device, DeviceAdmin)


class LinkAdmin(admin.ModelAdmin):
    fields = ('from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)
    raw_id_fields = ('from_device', 'to_device', 'from_interface', 'to_interface',)


admin.site.register(Link, LinkAdmin)


class TopologyAdmin(admin.ModelAdmin):
    fields = ('name', 'scale', 'panX', 'panY',)
    raw_id_fields = ()


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
