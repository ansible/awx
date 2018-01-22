from rest_framework import routers
from awx.network_ui import v2_api_views


router = routers.DefaultRouter()


router.register(r'device', v2_api_views.DeviceViewSet)
router.register(r'link', v2_api_views.LinkViewSet)
router.register(r'topology', v2_api_views.TopologyViewSet)
router.register(r'client', v2_api_views.ClientViewSet)
router.register(r'topologyhistory', v2_api_views.TopologyHistoryViewSet)
router.register(r'messagetype', v2_api_views.MessageTypeViewSet)
router.register(r'interface', v2_api_views.InterfaceViewSet)
router.register(r'group', v2_api_views.GroupViewSet)
router.register(r'groupdevice', v2_api_views.GroupDeviceViewSet)
router.register(r'databinding', v2_api_views.DataBindingViewSet)
router.register(r'datatype', v2_api_views.DataTypeViewSet)
router.register(r'datasheet', v2_api_views.DataSheetViewSet)
router.register(r'stream', v2_api_views.StreamViewSet)
router.register(r'process', v2_api_views.ProcessViewSet)
router.register(r'toolbox', v2_api_views.ToolboxViewSet)
router.register(r'toolboxitem', v2_api_views.ToolboxItemViewSet)
router.register(r'fsmtrace', v2_api_views.FSMTraceViewSet)
router.register(r'topologyinventory', v2_api_views.TopologyInventoryViewSet)
router.register(r'eventtrace', v2_api_views.EventTraceViewSet)
router.register(r'coverage', v2_api_views.CoverageViewSet)
router.register(r'topologysnapshot', v2_api_views.TopologySnapshotViewSet)
router.register(r'testcase', v2_api_views.TestCaseViewSet)
router.register(r'result', v2_api_views.ResultViewSet)
router.register(r'codeundertest', v2_api_views.CodeUnderTestViewSet)
router.register(r'testresult', v2_api_views.TestResultViewSet)
