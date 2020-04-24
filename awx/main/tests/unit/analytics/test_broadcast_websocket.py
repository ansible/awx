import datetime

from awx.main.analytics.broadcast_websocket import FixedSlidingWindow
from awx.main.analytics.broadcast_websocket import dt_to_seconds


class TestFixedSlidingWindow():

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

        assert 20 == fsw.render(self.ts(minute=0, second=19, microsecond=0)), \
            "A. The second of the last record() call"
        assert 20 == fsw.render(self.ts(minute=0, second=20, microsecond=0)), \
            "B. The second after the last record() call"
        assert 20 == fsw.render(self.ts(minute=0, second=59, microsecond=0)), \
            "C. Last second in the same minute that all record() called in"
        assert 20 == fsw.render(self.ts(minute=1, second=0, microsecond=0)), \
            "D. First second of the minute following the minute that all record() calls in"
        for i in range(20):
            assert 20 - i == fsw.render(self.ts(minute=1, second=i, microsecond=0)), \
                "E. Sliding window where 1 record() should drop from the results each time"

        assert 0 == fsw.render(self.ts(minute=1, second=20, microsecond=0)), \
            "F. First second one minute after all record() calls"
