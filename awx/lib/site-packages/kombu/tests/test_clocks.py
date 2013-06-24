from __future__ import absolute_import

from heapq import heappush

from kombu.clocks import LamportClock

from .utils import TestCase


class test_LamportClock(TestCase):

    def test_clocks(self):
        c1 = LamportClock()
        c2 = LamportClock()

        c1.forward()
        c2.forward()
        c1.forward()
        c1.forward()
        c2.adjust(c1.value)
        self.assertEqual(c2.value, c1.value + 1)
        self.assertTrue(repr(c1))

        c2_val = c2.value
        c2.forward()
        c2.forward()
        c2.adjust(c1.value)
        self.assertEqual(c2.value, c2_val + 2 + 1)

        c1.adjust(c2.value)
        self.assertEqual(c1.value, c2.value + 1)

    def test_sort(self):
        c = LamportClock()
        pid1 = 'a.example.com:312'
        pid2 = 'b.example.com:311'

        events = []

        m1 = (c.forward(), pid1)
        heappush(events, m1)
        m2 = (c.forward(), pid2)
        heappush(events, m2)
        m3 = (c.forward(), pid1)
        heappush(events, m3)
        m4 = (30, pid1)
        heappush(events, m4)
        m5 = (30, pid2)
        heappush(events, m5)

        self.assertEqual(str(c), str(c.value))

        self.assertEqual(c.sort_heap(events), m1)
        self.assertEqual(c.sort_heap([m4, m5]), m4)
        self.assertEqual(c.sort_heap([m4, m5, m1]), m4)
