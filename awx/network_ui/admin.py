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

from awx.network_ui.models import Toolbox

from awx.network_ui.models import ToolboxItem

from awx.network_ui.models import FSMTrace

from awx.network_ui.models import TopologyInventory

from awx.network_ui.models import EventTrace

from awx.network_ui.models import Coverage

from awx.network_ui.models import TopologySnapshot

from awx.network_ui.models import TestCase

from awx.network_ui.models import Result

from awx.network_ui.models import CodeUnderTest

from awx.network_ui.models import TestResult


class DeviceAdmin(admin.ModelAdmin):
    fields = ('topology', 'name', 'x', 'y', 'id', 'device_type', 'interface_id_seq', 'process_id_seq', 'host_id',)
    raw_id_fields = ('topology',)


admin.site.register(Device, DeviceAdmin)


class LinkAdmin(admin.ModelAdmin):
    fields = ('from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)
    raw_id_fields = ('from_device', 'to_device', 'from_interface', 'to_interface',)


admin.site.register(Link, LinkAdmin)


class TopologyAdmin(admin.ModelAdmin):
    fields = ('name', 'scale', 'panX', 'panY', 'device_id_seq', 'link_id_seq', 'group_id_seq', 'stream_id_seq',)
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


class GroupAdmin(admin.ModelAdmin):
    fields = ('id', 'name', 'x1', 'y1', 'x2', 'y2', 'topology', 'group_type', 'inventory_group_id',)
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
    fields = ('device', 'name', 'process_type', 'id',)
    raw_id_fields = ('device',)


admin.site.register(Process, ProcessAdmin)


class ToolboxAdmin(admin.ModelAdmin):
    fields = ('name',)
    raw_id_fields = ()


admin.site.register(Toolbox, ToolboxAdmin)


class ToolboxItemAdmin(admin.ModelAdmin):
    fields = ('toolbox', 'data',)
    raw_id_fields = ('toolbox',)


admin.site.register(ToolboxItem, ToolboxItemAdmin)


class FSMTraceAdmin(admin.ModelAdmin):
    fields = ('fsm_name', 'from_state', 'to_state', 'message_type', 'client', 'trace_session_id', 'order',)
    raw_id_fields = ('client',)


admin.site.register(FSMTrace, FSMTraceAdmin)


class TopologyInventoryAdmin(admin.ModelAdmin):
    fields = ('topology', 'inventory_id',)
    raw_id_fields = ('topology',)


admin.site.register(TopologyInventory, TopologyInventoryAdmin)


class EventTraceAdmin(admin.ModelAdmin):
    fields = ('client', 'trace_session_id', 'event_data', 'message_id',)
    raw_id_fields = ('client',)


admin.site.register(EventTrace, EventTraceAdmin)


class CoverageAdmin(admin.ModelAdmin):
    fields = ('coverage_data', 'test_result',)
    raw_id_fields = ('test_result',)


admin.site.register(Coverage, CoverageAdmin)


class TopologySnapshotAdmin(admin.ModelAdmin):
    fields = ('client', 'topology_id', 'trace_session_id', 'snapshot_data', 'order',)
    raw_id_fields = ('client', 'snapshot_data',)


admin.site.register(TopologySnapshot, TopologySnapshotAdmin)


class TestCaseAdmin(admin.ModelAdmin):
    fields = ('name', 'test_case_data',)
    raw_id_fields = ('name',)


admin.site.register(TestCase, TestCaseAdmin)


class ResultAdmin(admin.ModelAdmin):
    fields = ('name',)
    raw_id_fields = ()


admin.site.register(Result, ResultAdmin)


class CodeUnderTestAdmin(admin.ModelAdmin):
    fields = ('version_x', 'version_y', 'version_z', 'commits_since', 'commit_hash',)
    raw_id_fields = ('code_under_test_id',)


admin.site.register(CodeUnderTest, CodeUnderTestAdmin)


class TestResultAdmin(admin.ModelAdmin):
    fields = ('test_case', 'result', 'code_under_test', 'time', 'id', 'client',)
    raw_id_fields = ('test_case', 'result', 'code_under_test', 'client',)


admin.site.register(TestResult, TestResultAdmin)
