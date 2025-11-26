# -*- coding: utf-8 -*-

# Copyright (c) 2025 Ansible, Inc.
# All Rights Reserved

"""Redis client utilities with automatic retry on connection errors."""

import redis
import redis.asyncio
from django.conf import settings
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError


def _get_redis_pool_kwargs():
    """
    Get common Redis connection pool kwargs with retry configuration.

    Returns:
        dict: Keyword arguments for redis.ConnectionPool.from_url()
    """
    retry = Retry(ExponentialBackoff(cap=settings.REDIS_BACKOFF_CAP, base=settings.REDIS_BACKOFF_BASE), retries=settings.REDIS_RETRY_COUNT)
    return {
        'retry': retry,
        'retry_on_error': [BusyLoadingError, ConnectionError, TimeoutError],
    }


def get_redis_client():
    """
    Create a Redis client with automatic retry on connection errors.

    This function creates a Redis connection with built-in retry logic to handle
    transient connection failures (like broken pipes, timeouts, etc.) that can occur
    during long-running operations.

    Based on PR feedback: https://github.com/ansible/awx/pull/16158#issuecomment-3486839154
    Uses redis-py's built-in retry mechanism instead of custom retry logic.

    Returns:
        redis.Redis: A Redis client instance configured with retry logic

    Notes:
        - Uses exponential backoff with configurable retries (REDIS_RETRY_COUNT setting)
        - Retries on BusyLoadingError, ConnectionError, and TimeoutError
        - Requires redis-py 7.0+
    """
    pool = redis.ConnectionPool.from_url(
        settings.BROKER_URL,
        **_get_redis_pool_kwargs(),
    )
    return redis.Redis(connection_pool=pool)


def get_redis_client_async():
    """
    Create an async Redis client with automatic retry on connection errors.

    This is the async version of get_redis_client() for use with asyncio code.

    Returns:
        redis.asyncio.Redis: An async Redis client instance configured with retry logic

    Notes:
        - Uses exponential backoff with configurable retries (REDIS_RETRY_COUNT setting)
        - Retries on BusyLoadingError, ConnectionError, and TimeoutError
        - Requires redis-py 7.0+
    """
    pool = redis.asyncio.ConnectionPool.from_url(
        settings.BROKER_URL,
        **_get_redis_pool_kwargs(),
    )
    return redis.asyncio.Redis(connection_pool=pool)
