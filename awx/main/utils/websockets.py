import asyncio
import json
import logging

from django.core.serializers.json import DjangoJSONEncoder

from channels.layers import get_channel_layer

logger = logging.getLogger('awx.main.utils.websockets')

__all__ = ["emit_websocket_payload"]


def emit_websocket_payload(group, payload):
    try:
        payload_dumped = json.dumps(payload, cls=DjangoJSONEncoder)
    except ValueError:
        logger.error("Invalid payload to emit")
        return

    channel_layer = get_channel_layer()

    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(
        channel_layer.group_send(
            group,
            {"type": "internal.message", "text": payload_dumped, "needs_relay": True},
        )
    )
    event_loop.close()
