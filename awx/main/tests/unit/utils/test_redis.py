# -*- coding: utf-8 -*-

# Copyright (c) 2025 Ansible, Inc.
# All Rights Reserved

from django.test.utils import override_settings

from awx.main.utils.redis import get_redis_client, get_redis_client_async
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.backoff import ExponentialBackoff


class TestRedisRetryConfiguration:
    """Verify Redis retry configuration is applied to connection objects."""

    def test_retry_configuration_applied_to_client(self, settings):
        """Verify all retry settings are applied to the connection pool."""
        # Test sync client
        client = get_redis_client()
        retry = client.connection_pool.connection_kwargs['retry']
        backoff = retry._backoff
        retry_errors = client.connection_pool.connection_kwargs['retry_on_error']

        # Assert provided values match values on the object
        assert retry._retries == settings.REDIS_RETRY_COUNT == 3
        assert isinstance(backoff, ExponentialBackoff)
        assert backoff._base == 0.5
        assert backoff._cap == 1.0
        assert BusyLoadingError in retry_errors
        assert ConnectionError in retry_errors
        assert TimeoutError in retry_errors

        # Test async client has same config
        client_async = get_redis_client_async()
        retry_async = client_async.connection_pool.connection_kwargs['retry']
        backoff_async = retry_async._backoff
        retry_errors_async = client_async.connection_pool.connection_kwargs['retry_on_error']

        assert retry_async._retries == settings.REDIS_RETRY_COUNT
        assert backoff_async._base == 0.5
        assert backoff_async._cap == 1.0
        assert ConnectionError in retry_errors_async

    @override_settings(REDIS_RETRY_COUNT=5)
    def test_override_settings_applied_to_client(self):
        """Verify override_settings changes are applied to client object."""
        from importlib import reload
        import awx.main.utils.redis as redis_module

        reload(redis_module)
        from awx.main.utils.redis import get_redis_client as get_client_new

        client = get_client_new()
        retry = client.connection_pool.connection_kwargs['retry']

        # Assert provided value (5) matches value on object
        assert retry._retries == 5
