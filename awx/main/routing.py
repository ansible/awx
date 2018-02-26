from channels.routing import route
from awx.network_ui.routing import channel_routing as network_routing


channel_routing = [
    route("websocket.connect", "awx.main.consumers.ws_connect", path=r'^/websocket/$'),
    route("websocket.disconnect", "awx.main.consumers.ws_disconnect", path=r'^/websocket/$'),
    route("websocket.receive", "awx.main.consumers.ws_receive", path=r'^/websocket/$'),
]


channel_routing += network_routing
