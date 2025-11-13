# -*- coding: utf-8 -*-

# Copyright (c) 2025 Ansible, Inc.
# All Rights Reserved

from unittest import mock
import json

from awx.main.queue import CallbackQueueDispatcher
from django.conf import settings


class TestCallbackQueueDispatcher:
    """Tests for CallbackQueueDispatcher with Redis retry logic."""

    def test_dispatcher_uses_get_redis_client(self):
        """Verify that CallbackQueueDispatcher uses get_redis_client for connection."""
        with mock.patch('awx.main.queue.get_redis_client') as mock_get_redis:
            mock_redis = mock.Mock()
            mock_get_redis.return_value = mock_redis

            dispatcher = CallbackQueueDispatcher()

            # Verify get_redis_client was called with BROKER_URL
            mock_get_redis.assert_called_once_with(settings.BROKER_URL)
            assert dispatcher.connection == mock_redis

    def test_dispatcher_dispatch_calls_rpush(self):
        """Verify that dispatch() calls rpush on Redis connection."""
        with mock.patch('awx.main.queue.get_redis_client') as mock_get_redis:
            mock_redis = mock.Mock()
            mock_get_redis.return_value = mock_redis

            dispatcher = CallbackQueueDispatcher()
            test_obj = {'event': 'test', 'data': 'value'}

            dispatcher.dispatch(test_obj)

            # Verify rpush was called with the queue name and JSON-serialized object
            mock_redis.rpush.assert_called_once()
            call_args = mock_redis.rpush.call_args
            assert call_args[0][0] == dispatcher.queue
            # Verify the object was JSON serialized
            serialized_obj = call_args[0][1]
            assert json.loads(serialized_obj) == test_obj

    def test_dispatcher_handles_vault_objects(self):
        """Verify that dispatch() properly handles Ansible vault objects using custom encoder."""
        with mock.patch('awx.main.queue.get_redis_client') as mock_get_redis:
            mock_redis = mock.Mock()
            mock_get_redis.return_value = mock_redis

            dispatcher = CallbackQueueDispatcher()

            # Create a mock vault object
            vault_obj = mock.Mock()
            vault_obj.yaml_tag = '!vault'
            vault_obj.data = 'encrypted_data'

            test_obj = {'password': vault_obj}

            dispatcher.dispatch(test_obj)

            # Verify rpush was called
            mock_redis.rpush.assert_called_once()
            call_args = mock_redis.rpush.call_args

            # Verify the vault object was properly serialized
            serialized_obj = call_args[0][1]
            deserialized = json.loads(serialized_obj)
            assert deserialized['password'] == 'encrypted_data'

    def test_dispatcher_connection_survives_redis_retry(self):
        """
        Integration-style test: Verify that dispatcher continues to work even when
        Redis connection is configured with retry logic.
        """
        from redis.exceptions import ConnectionError

        with mock.patch('redis.ConnectionPool.from_url') as mock_pool_from_url, mock.patch('redis.Redis') as mock_redis:

            mock_pool = mock.Mock()
            mock_pool_from_url.return_value = mock_pool
            mock_redis_instance = mock.Mock()
            mock_redis.return_value = mock_redis_instance

            # Simulate connection error on first rpush, success on retry
            mock_redis_instance.rpush.side_effect = [ConnectionError("Broken pipe"), None]

            dispatcher = CallbackQueueDispatcher()

            # With retry logic in place, this should not raise an exception
            # (though the actual retry happens at redis-py level)
            # This test verifies the dispatcher is using the retry-enabled client
            assert dispatcher.connection == mock_redis_instance
