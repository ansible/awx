import redis
import logging

from django.conf import settings
from django.urls import re_path

from channels.routing import ProtocolTypeRouter, URLRouter

from ansible_base.lib.channels.middleware import DrfAuthMiddlewareStack

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
            logger.warning("encountered an error communicating with redis.")
            raise e
        super().__init__(*args, **kwargs)


class MultipleURLRouterAdapter:
    """
    Django channels doesn't nicely support Auth_1(urls_1), Auth_2(urls_2), ..., Auth_n(urls_n)
    This class allows assocating a websocket url with an auth
    Ordering matters. The first matching url will be used.
    """

    def __init__(self, *auths):
        self._auths = [a for a in auths]

    async def __call__(self, scope, receive, send):
        """
        Loop through the list of passed in URLRouter's (they may or may not be wrapped by auth).
        We know we have exhausted the list of URLRouter patterns when we get a
        ValueError('No route found for path %s'). When that happens, move onto the next
        URLRouter.
        If the final URLRouter raises an error, re-raise it in the end.

        We know that we found a match when no error is raised, end the loop.
        """
        last_index = len(self._auths) - 1
        for i, auth in enumerate(self._auths):
            try:
                return await auth.__call__(scope, receive, send)
            except ValueError as e:
                if str(e).startswith('No route found for path'):
                    # Only surface the error if on the last URLRouter
                    if i == last_index:
                        raise


websocket_urlpatterns = [
    re_path(r'api/websocket/$', consumers.EventConsumer.as_asgi()),
    re_path(r'websocket/$', consumers.EventConsumer.as_asgi()),
]
websocket_relay_urlpatterns = [
    re_path(r'websocket/relay/$', consumers.RelayConsumer.as_asgi()),
]

application = AWXProtocolTypeRouter(
    {
        'websocket': MultipleURLRouterAdapter(
            URLRouter(websocket_relay_urlpatterns),
            DrfAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
        )
    }
)
