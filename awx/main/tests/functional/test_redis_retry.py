# -*- coding: utf-8 -*-

# Copyright (c) 2025 Ansible, Inc.
# All Rights Reserved

import pytest
from unittest import mock

from django.conf import settings


class TestRedisRetryIntegration:
    """
    Integration tests for Redis retry functionality across different components.
    These tests verify that all components properly use get_redis_client().
    """

    def test_callback_queue_dispatcher_uses_retry_client(self):
        """Verify CallbackQueueDispatcher uses get_redis_client with retry logic."""
        from awx.main.queue import CallbackQueueDispatcher

        with mock.patch('awx.main.queue.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_get_client.return_value = mock_redis

            dispatcher = CallbackQueueDispatcher()

            mock_get_client.assert_called_once_with(settings.BROKER_URL)
            assert dispatcher.connection == mock_redis

    def test_routing_awx_protocol_type_router_uses_retry_client(self):
        """Verify AWXProtocolTypeRouter uses get_redis_client for cleanup."""
        from awx.main.routing import AWXProtocolTypeRouter

        with mock.patch('awx.main.routing.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_redis.scan_iter.return_value = []
            mock_get_client.return_value = mock_redis

            AWXProtocolTypeRouter({})

            mock_get_client.assert_called_once_with(settings.BROKER_URL)
            mock_redis.scan_iter.assert_called_once_with('asgi:*', 500)

    @pytest.mark.asyncio
    async def test_consumers_relay_consumer_uses_retry_client(self, fake_redis):
        """Verify RelayConsumer uses get_redis_client_async when handling metrics."""
        from awx.main.consumers import RelayConsumer
        import json

        with mock.patch('awx.main.consumers.get_redis_client_async') as mock_get_async_client:
            mock_redis = mock.AsyncMock()
            mock_get_async_client.return_value = mock_redis

            consumer = RelayConsumer()
            consumer.channel_layer = mock.Mock()
            consumer.channel_layer.group_send = mock.AsyncMock()

            # Simulate receiving metrics data in correct format
            metrics_message = {'text': json.dumps({'metrics_namespace': 'test', 'instance': 'instance1', 'metrics': {'count': 42}})}
            metrics_data = ('metrics', metrics_message)

            # Mock unwrap_broadcast_msg to return our data
            with mock.patch('awx.main.consumers.unwrap_broadcast_msg', return_value=metrics_data):
                # Call receive_json which should use get_redis_client_async for metrics
                await consumer.receive_json({})
                mock_get_async_client.assert_called_with(settings.BROKER_URL)
                mock_redis.set.assert_called_once()

    def test_dispatch_control_status_uses_retry_client(self, fake_redis):
        """Verify Control.status() uses get_redis_client."""
        from awx.main.dispatch.control import Control

        with mock.patch('awx.main.dispatch.control.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_redis.get.return_value = b'test_stats'
            mock_redis.keys.return_value = [b'awx_callback_receiver_statistics_1']
            mock_get_client.return_value = mock_redis

            control = Control('dispatcher')
            stats = control.status()

            mock_get_client.assert_called_once_with(settings.BROKER_URL)
            assert stats == 'test_stats'

    def test_subsystem_metrics_uses_retry_client(self, fake_redis):
        """Verify subsystem metrics use get_redis_client for pipeline and connection."""
        from awx.main.analytics.subsystem_metrics import Metrics

        with mock.patch('awx.main.analytics.subsystem_metrics.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_pipeline = mock.Mock()
            mock_redis.pipeline.return_value = mock_pipeline
            mock_get_client.return_value = mock_redis

            metrics = Metrics('test_namespace', auto_pipe_execute=False)

            # get_redis_client should be called twice: once for pipe, once for conn
            assert mock_get_client.call_count == 2
            assert metrics.pipe == mock_pipeline
            assert metrics.conn == mock_redis

    def test_broadcast_websocket_stats_sync_uses_retry_client(self, fake_redis):
        """Verify broadcast websocket get_stats_sync uses get_redis_client."""
        from awx.main.analytics.broadcast_websocket import RelayWebsocketStatsManager

        with mock.patch('awx.main.analytics.broadcast_websocket.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_redis.get.return_value = b''
            mock_get_client.return_value = mock_redis

            RelayWebsocketStatsManager.get_stats_sync()

            mock_get_client.assert_called_once_with(settings.BROKER_URL)
            mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_websocket_async_uses_retry_client(self, fake_redis):
        """Verify broadcast websocket async run_loop uses get_redis_client_async."""
        from awx.main.analytics.broadcast_websocket import RelayWebsocketStatsManager
        import asyncio

        with mock.patch('awx.main.analytics.broadcast_websocket.get_redis_client_async') as mock_get_async_client:
            mock_redis = mock.Mock()
            mock_redis.set = mock.AsyncMock()
            mock_get_async_client.return_value = mock_redis

            manager = RelayWebsocketStatsManager('test_hostname')

            # Run one iteration of the loop
            task = asyncio.create_task(manager.run_loop())

            # Let it run briefly then cancel
            await asyncio.sleep(0.1)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify async client was called
            mock_get_async_client.assert_called_with(settings.BROKER_URL)

    @pytest.mark.django_db
    def test_callback_broker_worker_uses_retry_client(self, fake_redis):
        """Verify CallbackBrokerWorker uses get_redis_client."""
        from awx.main.dispatch.worker.callback import CallbackBrokerWorker

        with mock.patch('awx.main.dispatch.worker.callback.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_redis.keys.return_value = []
            mock_redis.delete = mock.Mock()
            mock_get_client.return_value = mock_redis

            worker = CallbackBrokerWorker()

            mock_get_client.assert_called_once_with(settings.BROKER_URL)
            assert worker.redis == mock_redis

    @pytest.mark.django_db
    def test_awx_consumer_base_uses_retry_client(self, fake_redis):
        """Verify AWXConsumerBase uses get_redis_client."""
        from awx.main.dispatch.worker.base import AWXConsumerBase, BaseWorker

        with mock.patch('awx.main.dispatch.worker.base.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_get_client.return_value = mock_redis

            mock_worker = mock.Mock(spec=BaseWorker)
            mock_worker.work_loop = mock.Mock()

            consumer = AWXConsumerBase('test', mock_worker, queues=['test_queue'])

            mock_get_client.assert_called_once_with(settings.BROKER_URL)
            assert consumer.redis == mock_redis

    def test_instance_local_health_check_uses_retry_client(self, fake_redis):
        """Verify Instance.local_health_check() uses get_redis_client."""
        from awx.main.models.ha import Instance

        with mock.patch('awx.main.models.ha.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_redis.ping.return_value = True
            mock_get_client.return_value = mock_redis

            # Create instance without saving
            instance = Instance(hostname='test_instance', uuid='test-uuid-1234')

            # Mock save_health_data to avoid DB interaction
            with mock.patch.object(instance, 'save_health_data'):
                instance.local_health_check()

            mock_get_client.assert_called_once_with(settings.BROKER_URL)
            mock_redis.ping.assert_called_once()

    def test_routing_cleanup_executes_with_retry_client(self, fake_redis):
        """Verify AWXProtocolTypeRouter cleanup actually executes with retry client."""
        from awx.main.routing import AWXProtocolTypeRouter

        # Execute without mocking get_redis_client to hit actual code path
        # FakeRedis from conftest handles the Redis calls
        AWXProtocolTypeRouter({})

    def test_control_status_callback_receiver_path(self, fake_redis):
        """Verify Control.status() for callback_receiver service executes correctly."""
        from awx.main.dispatch.control import Control

        with mock.patch('awx.main.dispatch.control.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_redis.keys.return_value = [b'awx_callback_receiver_statistics_1', b'awx_callback_receiver_statistics_2']
            mock_redis.get.side_effect = [b'worker1_stats', b'worker2_stats']
            mock_get_client.return_value = mock_redis

            control = Control('callback_receiver')
            stats = control.status()

            # Should have called keys to find workers
            mock_redis.keys.assert_called_once_with('awx_callback_receiver_statistics_*')
            # Should have called get for each worker
            assert mock_redis.get.call_count == 2
            # Stats should be combined
            assert 'worker1_stats' in stats
            assert 'worker2_stats' in stats

    @pytest.mark.asyncio
    async def test_consumers_non_metrics_path(self, fake_redis):
        """Verify RelayConsumer handles non-metrics messages correctly."""
        from awx.main.consumers import RelayConsumer
        import json

        consumer = RelayConsumer()
        consumer.channel_layer = mock.Mock()
        consumer.channel_layer.group_send = mock.AsyncMock()

        # Non-metrics message
        non_metrics_message = {'text': json.dumps({'job_id': 123})}
        non_metrics_data = ('jobs', non_metrics_message)

        # Mock unwrap_broadcast_msg
        with mock.patch('awx.main.consumers.unwrap_broadcast_msg', return_value=non_metrics_data):
            await consumer.receive_json({})
            # Should have called group_send, not Redis
            consumer.channel_layer.group_send.assert_called_once()


class TestRedisRetryRegression:
    """
    Regression tests to ensure normal operations are unaffected by retry changes.
    """

    def test_normal_redis_operations_unaffected(self, fake_redis):
        """Verify normal Redis operations work as expected with retry configuration."""
        from awx.main.queue import CallbackQueueDispatcher

        with mock.patch('awx.main.queue.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_get_client.return_value = mock_redis

            dispatcher = CallbackQueueDispatcher()
            test_obj = {'event': 'test', 'counter': 1}

            # Normal dispatch should work without issues
            dispatcher.dispatch(test_obj)

            mock_redis.rpush.assert_called_once()

    def test_short_duration_operations_unaffected(self, fake_redis):
        """Verify short-duration operations complete normally with retry config."""
        from awx.main.models.ha import Instance

        with mock.patch('awx.main.models.ha.get_redis_client') as mock_get_client:
            mock_redis = mock.Mock()
            mock_redis.ping.return_value = True
            mock_get_client.return_value = mock_redis

            instance = Instance(hostname='test', uuid='test-uuid')

            with mock.patch.object(instance, 'save_health_data'):
                # Quick health check should complete normally
                instance.local_health_check()

            # Should complete in single call (no retries needed)
            mock_redis.ping.assert_called_once()

    def test_actual_execution_without_mocking(self, fake_redis):
        """Test actual code execution paths without mocking get_redis_client."""
        from awx.main.queue import CallbackQueueDispatcher

        # This will execute the real get_redis_client code
        # FakeRedis from conftest handles the Redis operations
        dispatcher = CallbackQueueDispatcher()

        # Verify dispatcher was created successfully
        assert dispatcher is not None
        assert dispatcher.connection is not None

        # Test dispatch works
        dispatcher.dispatch({'test': 'data'})

    def test_subsystem_metrics_actual_init(self, fake_redis):
        """Test subsystem metrics initialization executes actual code paths."""
        from awx.main.analytics.subsystem_metrics import Metrics

        # Execute actual initialization without mocking
        metrics = Metrics('test_namespace', auto_pipe_execute=False)

        assert metrics is not None
        assert metrics.pipe is not None
        assert metrics.conn is not None

    @pytest.mark.django_db
    def test_callback_broker_worker_actual_init(self, fake_redis):
        """Test CallbackBrokerWorker initialization executes actual code."""
        from awx.main.dispatch.worker.callback import CallbackBrokerWorker

        # Execute actual initialization
        worker = CallbackBrokerWorker()

        assert worker is not None
        assert worker.redis is not None

    @pytest.mark.django_db
    def test_awx_consumer_base_actual_init(self, fake_redis):
        """Test AWXConsumerBase initialization executes actual code."""
        from awx.main.dispatch.worker.base import AWXConsumerBase, BaseWorker

        mock_worker = mock.Mock(spec=BaseWorker)
        mock_worker.work_loop = mock.Mock()

        # Execute actual initialization
        consumer = AWXConsumerBase('test', mock_worker, queues=['test'])

        assert consumer is not None
        assert consumer.redis is not None
