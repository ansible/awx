from rest_framework import routers
from awx.network_ui import v2_api_views


router = routers.DefaultRouter()


router.register(r'device', v2_api_views.DeviceViewSet)
router.register(r'link', v2_api_views.LinkViewSet)
router.register(r'topology', v2_api_views.TopologyViewSet)
router.register(r'interface', v2_api_views.InterfaceViewSet)
router.register(r'group', v2_api_views.GroupViewSet)
router.register(r'groupdevice', v2_api_views.GroupDeviceViewSet)
router.register(r'stream', v2_api_views.StreamViewSet)
router.register(r'process', v2_api_views.ProcessViewSet)
router.register(r'toolbox', v2_api_views.ToolboxViewSet)
router.register(r'toolboxitem', v2_api_views.ToolboxItemViewSet)
router.register(r'topologyinventory', v2_api_views.TopologyInventoryViewSet)
