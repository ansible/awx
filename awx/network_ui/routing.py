from channels.routing import route
from awx.network_ui.consumers import ws_connect, ws_message, ws_disconnect, console_printer, persistence, discovery
from awx.network_ui.consumers import ansible_connect, ansible_message, ansible_disconnect
from awx.network_ui.consumers import worker_connect, worker_message, worker_disconnect
from awx.network_ui.consumers import tester_connect, tester_message, tester_disconnect

channel_routing = [
    route("websocket.connect", ws_connect, path=r"^/network_ui/topology"),
    route("websocket.receive", ws_message, path=r"^/network_ui/topology"),
    route("websocket.disconnect", ws_disconnect, path=r"^/network_ui/topology"),
    route("websocket.connect", ansible_connect, path=r"^/network_ui/ansible"),
    route("websocket.receive", ansible_message, path=r"^/network_ui/ansible"),
    route("websocket.disconnect", ansible_disconnect, path=r"^/network_ui/ansible"),
    route("websocket.connect", worker_connect, path=r"^/network_ui/worker"),
    route("websocket.receive", worker_message, path=r"^/network_ui/worker"),
    route("websocket.disconnect", worker_disconnect, path=r"^/network_ui/worker"),
    route("websocket.connect", tester_connect, path=r"^/network_ui/tester"),
    route("websocket.receive", tester_message, path=r"^/network_ui/tester"),
    route("websocket.disconnect", tester_disconnect, path=r"^/network_ui/tester"),
    route("console_printer", console_printer),
    route("persistence", persistence.handle),
    route("discovery", discovery.handle),
]
