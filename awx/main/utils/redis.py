import sys
import time

from django.conf import settings

import redis


def ping_redis():
    redis.Redis.from_url(settings.BROKER_URL).ping()


def exit_if_redis_down(logger):
    try:
        ping_redis()
    except redis.ConnectionError as exc:
        logger.info(f'Redis ping error: {exc}')
        time.sleep(1)  # Patience to avoid log spam
        sys.exit(1)
