from rest_framework import routers
from awx.network_ui import api_views


router = routers.DefaultRouter()


router.register(r'device', api_views.DeviceViewSet)
router.register(r'link', api_views.LinkViewSet)
router.register(r'topology', api_views.TopologyViewSet)
router.register(r'client', api_views.ClientViewSet)
router.register(r'topologyhistory', api_views.TopologyHistoryViewSet)
router.register(r'messagetype', api_views.MessageTypeViewSet)
router.register(r'interface', api_views.InterfaceViewSet)
router.register(r'group', api_views.GroupViewSet)
router.register(r'groupdevice', api_views.GroupDeviceViewSet)
router.register(r'databinding', api_views.DataBindingViewSet)
router.register(r'datatype', api_views.DataTypeViewSet)
router.register(r'datasheet', api_views.DataSheetViewSet)
router.register(r'stream', api_views.StreamViewSet)
router.register(r'process', api_views.ProcessViewSet)
router.register(r'toolbox', api_views.ToolboxViewSet)
router.register(r'toolboxitem', api_views.ToolboxItemViewSet)
router.register(r'fsmtrace', api_views.FSMTraceViewSet)
router.register(r'topologyinventory', api_views.TopologyInventoryViewSet)
router.register(r'eventtrace', api_views.EventTraceViewSet)
router.register(r'coverage', api_views.CoverageViewSet)
router.register(r'topologysnapshot', api_views.TopologySnapshotViewSet)
router.register(r'testcase', api_views.TestCaseViewSet)
router.register(r'result', api_views.ResultViewSet)
router.register(r'codeundertest', api_views.CodeUnderTestViewSet)
router.register(r'testresult', api_views.TestResultViewSet)
