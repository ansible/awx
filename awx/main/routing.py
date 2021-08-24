import redis
import logging

from django.urls import re_path
from django.conf import settings

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from . import consumers


logger = logging.getLogger('awx.main.routing')


class AWXProtocolTypeRouter(ProtocolTypeRouter):
    def __init__(self, *args, **kwargs):
        try:
            r = redis.Redis.from_url(settings.BROKER_URL)
            for k in r.scan_iter('asgi:*', 500):
                logger.debug(f"cleaning up Redis key {k}")
                r.delete(k)
        except redis.exceptions.RedisError as e:
            logger.warn("encountered an error communicating with redis.")
            raise e
        super().__init__(*args, **kwargs)


websocket_urlpatterns = [
    re_path(r'websocket/$', consumers.EventConsumer),
    re_path(r'websocket/broadcast/$', consumers.BroadcastConsumer),
]

application = AWXProtocolTypeRouter(
    {
        'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
