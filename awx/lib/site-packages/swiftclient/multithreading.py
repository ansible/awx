# Copyright (c) 2010-2012 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from itertools import chain
import sys
from time import sleep
from Queue import Queue
from threading import Thread
from traceback import format_exception

from swiftclient.exceptions import ClientException


class StopWorkerThreadSignal(object):
    pass


class QueueFunctionThread(Thread):
    """
    Calls `func`` for each item in ``queue``; ``func`` is called with a
    de-queued item as the first arg followed by ``*args`` and ``**kwargs``.

    Any exceptions raised by ``func`` are stored in :attr:`self.exc_infos`.

    If the optional kwarg ``store_results`` is specified, it must be a list and
    each result of invoking ``func`` will be appended to that list.

    Putting a :class:`StopWorkerThreadSignal` instance into queue will cause
    this thread to exit.
    """

    def __init__(self, queue, func, *args, **kwargs):
        """
        :param queue: A :class:`Queue` object from which work jobs will be
                      pulled.
        :param func: A callable which will be invoked with a dequeued item
                     followed by ``*args`` and ``**kwargs``.
        :param \*args: Optional positional arguments for ``func``.
        :param \*\*kwargs: Optional kwargs for func.  If the kwarg
                           ``store_results`` is specified, its value must be a
                           list, and every result from invoking ``func`` will
                           be appended to the supplied list.  The kwarg
                           ``store_results`` will not be passed into ``func``.
        """
        Thread.__init__(self)
        self.queue = queue
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.exc_infos = []
        self.store_results = kwargs.pop('store_results', None)

    def run(self):
        while True:
            item = self.queue.get()
            if isinstance(item, StopWorkerThreadSignal):
                break
            try:
                result = self.func(item, *self.args, **self.kwargs)
                if self.store_results is not None:
                    self.store_results.append(result)
            except Exception:
                self.exc_infos.append(sys.exc_info())


class QueueFunctionManager(object):
    """
    A context manager to handle the life-cycle of a single :class:`Queue`
    and a list of associated :class:`QueueFunctionThread` instances.

    This class is not usually instantiated directly.  Instead, call the
    :meth:`MultiThreadingManager.queue_manager` object method,
    which will return an instance of this class.

    When entering the context, ``thread_count`` :class:`QueueFunctionThread`
    instances are created and started.  The input queue is returned.  Inside
    the context, any work item put into the queue will get worked on by one of
    the :class:`QueueFunctionThread` instances.

    When the context is exited, all threads are sent a
    :class:`StopWorkerThreadSignal` instance and then all threads are waited
    upon.  Finally, any exceptions from any of the threads are reported on via
    the supplied ``thread_manager``'s :meth:`error` method.  If an
    ``error_counter`` list was supplied on instantiation, its first element is
    incremented once for every exception which occurred.
    """

    def __init__(self, func, thread_count, thread_manager, thread_args=None,
                 thread_kwargs=None, error_counter=None,
                 connection_maker=None):
        """
        :param func: The worker function which will be passed into each
                     :class:`QueueFunctionThread`'s constructor.
        :param thread_count: The number of worker threads to run.
        :param thread_manager: An instance of :class:`MultiThreadingManager`.
        :param thread_args: Optional positional arguments to be passed into
                            each invocation of ``func`` after the de-queued
                            work item.
        :param thread_kwargs: Optional keyword arguments to be passed into each
                              invocation of ``func``.  If a list is supplied as
                              the ``store_results`` keyword argument, it will
                              be filled with every result of invoking ``func``
                              in all threads.
        :param error_counter: Optional list containing one integer.  If
                              supplied, the list's first element will be
                              incremented once for each exception in any
                              thread.  This happens only when exiting the
                              context.
        :param connection_maker: Optional callable.  If supplied, this callable
                                 will be invoked once per created thread, and
                                 the result will be passed into func after the
                                 de-queued work item but before ``thread_args``
                                 and ``thread_kwargs``.  This is used to ensure
                                 each thread has its own connection to Swift.
        """
        self.func = func
        self.thread_count = thread_count
        self.thread_manager = thread_manager
        self.error_counter = error_counter
        self.connection_maker = connection_maker
        self.queue = Queue(10000)
        self.thread_list = []
        self.thread_args = thread_args if thread_args else ()
        self.thread_kwargs = thread_kwargs if thread_kwargs else {}

    def __enter__(self):
        for _junk in range(self.thread_count):
            if self.connection_maker:
                thread_args = (self.connection_maker(),) + self.thread_args
            else:
                thread_args = self.thread_args
            qf_thread = QueueFunctionThread(self.queue, self.func,
                                            *thread_args, **self.thread_kwargs)
            qf_thread.start()
            self.thread_list.append(qf_thread)
        return self.queue

    def __exit__(self, exc_type, exc_value, traceback):
        for thread in [t for t in self.thread_list if t.isAlive()]:
            self.queue.put(StopWorkerThreadSignal())

        while any(map(QueueFunctionThread.is_alive, self.thread_list)):
            sleep(0.05)

        for thread in self.thread_list:
            for info in thread.exc_infos:
                if self.error_counter:
                    self.error_counter[0] += 1
                if isinstance(info[1], ClientException):
                    self.thread_manager.error(str(info[1]))
                else:
                    self.thread_manager.error(''.join(format_exception(*info)))


class MultiThreadingManager(object):
    """
    One object to manage context for multi-threading.  This should make
    bin/swift less error-prone and allow us to test this code.

    This object is a context manager and returns itself into the context.  When
    entering the context, two printing threads are created (see below) and they
    are waited on and cleaned up when exiting the context.

    A convenience method, :meth:`queue_manager`, is provided to create a
    :class:`QueueFunctionManager` context manager (a thread-pool with an
    associated input queue for work items).

    Also, thread-safe printing to two streams is provided.  The
    :meth:`print_msg` method will print to the supplied ``print_stream``
    (defaults to ``sys.stdout``) and the :meth:`error` method will print to the
    supplied ``error_stream`` (defaults to ``sys.stderr``).  Both of these
    printing methods will format the given string with any supplied ``*args``
    (a la printf) and encode the result to utf8 if necessary.

    The attribute :attr:`self.error_count` is incremented once per error
    message printed, so an application can tell if any worker threads
    encountered exceptions or otherwise called :meth:`error` on this instance.
    The swift command-line tool uses this to exit non-zero if any error strings
    were printed.
    """

    def __init__(self, print_stream=sys.stdout, error_stream=sys.stderr):
        """
        :param print_stream: The stream to which :meth:`print_msg` sends
                             formatted messages, encoded to utf8 if necessary.
        :param error_stream: The stream to which :meth:`error` sends formatted
                             messages, encoded to utf8 if necessary.
        """
        self.print_stream = print_stream
        self.printer = QueueFunctionManager(self._print, 1, self)
        self.error_stream = error_stream
        self.error_printer = QueueFunctionManager(self._print_error, 1, self)
        self.error_count = 0

    def __enter__(self):
        self.printer.__enter__()
        self.error_printer.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.error_printer.__exit__(exc_type, exc_value, traceback)
        self.printer.__exit__(exc_type, exc_value, traceback)

    def queue_manager(self, func, thread_count, *args, **kwargs):
        connection_maker = kwargs.pop('connection_maker', None)
        error_counter = kwargs.pop('error_counter', None)
        return QueueFunctionManager(func, thread_count, self, thread_args=args,
                                    thread_kwargs=kwargs,
                                    connection_maker=connection_maker,
                                    error_counter=error_counter)

    def print_msg(self, msg, *fmt_args):
        if fmt_args:
            msg = msg % fmt_args
        self.printer.queue.put(msg)

    def print_items(self, items, offset=14, skip_missing=False):
        lines = []
        template = '%%%ds: %%s' % offset
        for k, v in items:
            if skip_missing and not v:
                continue
            lines.append((template % (k, v)).rstrip())
        self.print_msg('\n'.join(lines))

    def print_headers(self, headers, meta_prefix='', exclude_headers=None,
                      offset=14):
        exclude_headers = exclude_headers or []
        meta_headers = []
        other_headers = []
        template = '%%%ds: %%s' % offset
        for key, value in headers.items():
            if key.startswith(meta_prefix):
                meta_key = 'Meta %s' % key[len(meta_prefix):].title()
                meta_headers.append(template % (meta_key, value))
            elif key not in exclude_headers:
                other_headers.append(template % (key.title(), value))
        self.print_msg('\n'.join(chain(meta_headers, other_headers)))

    def error(self, msg, *fmt_args):
        if fmt_args:
            msg = msg % fmt_args
        self.error_printer.queue.put(msg)

    def _print(self, item, stream=None):
        if stream is None:
            stream = self.print_stream
        if isinstance(item, unicode):
            item = item.encode('utf8')
        print >>stream, item

    def _print_error(self, item):
        self.error_count += 1
        return self._print(item, stream=self.error_stream)
