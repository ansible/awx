from channels.routing import route


channel_routing = [
    route("websocket.connect", "awx.main.consumers.job_event_connect", path=r'^/job_event/(?P<id>[a-zA-Z0-9_]+)/$'),
]
