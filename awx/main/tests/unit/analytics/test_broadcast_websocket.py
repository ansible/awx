import datetime
from unittest.mock import Mock, patch

from awx.main.analytics.broadcast_websocket import FixedSlidingWindow, RelayWebsocketStatsManager
from awx.main.analytics.broadcast_websocket import dt_to_seconds


class TestFixedSlidingWindow:
    def ts(self, **kwargs):
        e = {
            'year': 1985,
            'month': 1,
            'day': 1,
            'hour': 1,
        }
        return dt_to_seconds(datetime.datetime(**kwargs, **e))

    def test_record_same_minute(self):
        """
        Legend:
                - = record()
                ^ = render()
                |---| = 1 minute, 60 seconds

         ....................
        |------------------------------------------------------------|
         ^^^^^^^^^^^^^^^^^^^^
        """

        fsw = FixedSlidingWindow(self.ts(minute=0, second=0, microsecond=0))
        for i in range(20):
            fsw.record(self.ts(minute=0, second=i, microsecond=0))
            assert (i + 1) == fsw.render(self.ts(minute=0, second=i, microsecond=0))

    def test_record_same_minute_render_diff_minute(self):
        """
        Legend:
                - = record()
                ^ = render()
                |---| = 1 minute, 60 seconds

         ....................
        |------------------------------------------------------------|
                            ^^                                      ^
                            AB                                      C
        |------------------------------------------------------------|
         ^^^^^^^^^^^^^^^^^^^^^
         DEEEEEEEEEEEEEEEEEEEF
        """

        fsw = FixedSlidingWindow(self.ts(minute=0, second=0, microsecond=0))
        for i in range(20):
            fsw.record(self.ts(minute=0, second=i, microsecond=0))

        assert 20 == fsw.render(self.ts(minute=0, second=19, microsecond=0)), "A. The second of the last record() call"
        assert 20 == fsw.render(self.ts(minute=0, second=20, microsecond=0)), "B. The second after the last record() call"
        assert 20 == fsw.render(self.ts(minute=0, second=59, microsecond=0)), "C. Last second in the same minute that all record() called in"
        assert 20 == fsw.render(self.ts(minute=1, second=0, microsecond=0)), "D. First second of the minute following the minute that all record() calls in"
        for i in range(20):
            assert 20 - i == fsw.render(self.ts(minute=1, second=i, microsecond=0)), "E. Sliding window where 1 record() should drop from the results each time"

        assert 0 == fsw.render(self.ts(minute=1, second=20, microsecond=0)), "F. First second one minute after all record() calls"


class TestRelayWebsocketStatsManager:
    """Test Redis client caching in RelayWebsocketStatsManager."""

    def test_get_stats_sync_caches_redis_client(self):
        """Verify get_stats_sync caches Redis client to avoid creating new connection pools."""
        # Reset class variable
        RelayWebsocketStatsManager._redis_client = None

        mock_redis = Mock()
        mock_redis.get.return_value = b''

        with patch('awx.main.analytics.broadcast_websocket.get_redis_client', return_value=mock_redis) as mock_get_client:
            # First call should create client
            RelayWebsocketStatsManager.get_stats_sync()
            assert mock_get_client.call_count == 1

            # Second call should reuse cached client
            RelayWebsocketStatsManager.get_stats_sync()
            assert mock_get_client.call_count == 1  # Still 1, not called again

            # Third call should still reuse cached client
            RelayWebsocketStatsManager.get_stats_sync()
            assert mock_get_client.call_count == 1

        # Cleanup
        RelayWebsocketStatsManager._redis_client = None

    def test_get_stats_sync_returns_parsed_metrics(self):
        """Verify get_stats_sync returns parsed metric families from Redis."""
        # Reset class variable
        RelayWebsocketStatsManager._redis_client = None

        # Sample Prometheus metrics format
        sample_metrics = b'# HELP test_metric A test metric\n# TYPE test_metric gauge\ntest_metric 42\n'

        mock_redis = Mock()
        mock_redis.get.return_value = sample_metrics

        with patch('awx.main.analytics.broadcast_websocket.get_redis_client', return_value=mock_redis):
            result = list(RelayWebsocketStatsManager.get_stats_sync())

            # Should return parsed metric families
            assert len(result) > 0
            assert mock_redis.get.called

        # Cleanup
        RelayWebsocketStatsManager._redis_client = None

    def test_get_stats_sync_handles_empty_redis_data(self):
        """Verify get_stats_sync handles empty data from Redis gracefully."""
        # Reset class variable
        RelayWebsocketStatsManager._redis_client = None

        mock_redis = Mock()
        mock_redis.get.return_value = None  # Redis returns None when key doesn't exist

        with patch('awx.main.analytics.broadcast_websocket.get_redis_client', return_value=mock_redis):
            result = list(RelayWebsocketStatsManager.get_stats_sync())

            # Should handle empty data gracefully
            assert result == []
            assert mock_redis.get.called

        # Cleanup
        RelayWebsocketStatsManager._redis_client = None
