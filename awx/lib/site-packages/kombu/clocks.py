"""
kombu.clocks
============

Logical Clocks and Synchronization.

"""
from __future__ import absolute_import
from __future__ import with_statement

import threading

from itertools import islice, izip

__all__ = ['LamportClock']


class LamportClock(object):
    """Lamport's logical clock.

    From Wikipedia:

    A Lamport logical clock is a monotonically incrementing software counter
    maintained in each process.  It follows some simple rules:

        * A process increments its counter before each event in that process;
        * When a process sends a message, it includes its counter value with
          the message;
        * On receiving a message, the receiver process sets its counter to be
          greater than the maximum of its own value and the received value
          before it considers the message received.

    Conceptually, this logical clock can be thought of as a clock that only
    has meaning in relation to messages moving between processes.  When a
    process receives a message, it resynchronizes its logical clock with
    the sender.

    .. seealso::

        * `Lamport timestamps`_

        * `Lamports distributed mutex`_

    .. _`Lamport Timestamps`: http://en.wikipedia.org/wiki/Lamport_timestamps
    .. _`Lamports distributed mutex`: http://bit.ly/p99ybE

    *Usage*

    When sending a message use :meth:`forward` to increment the clock,
    when receiving a message use :meth:`adjust` to sync with
    the time stamp of the incoming message.

    """
    #: The clocks current value.
    value = 0

    def __init__(self, initial_value=0):
        self.value = initial_value
        self.mutex = threading.Lock()

    def adjust(self, other):
        with self.mutex:
            self.value = max(self.value, other) + 1
            return self.value

    def forward(self):
        with self.mutex:
            self.value += 1
            return self.value

    def sort_heap(self, h):
        """List of tuples containing at least two elements, representing
        an event, where the first element is the event's scalar clock value,
        and the second element is the id of the process (usually
        ``"hostname:pid"``): ``sh([(clock, processid, ...?), (...)])``

        The list must already be sorted, which is why we refer to it as a
        heap.

        The tuple will not be unpacked, so more than two elements can be
        present.  Returns the latest event.

        """
        if h[0][0] == h[1][0]:
            same = []
            for PN in izip(h, islice(h, 1, None)):
                if PN[0][0] != PN[1][0]:
                    break  # Prev and Next's clocks differ
                same.append(PN[0])
            # return first item sorted by process id
            return sorted(same, key=lambda event: event[1])[0]
        # clock values unique, return first item
        return h[0]

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return '<LamportClock: %r>' % (self.value, )
