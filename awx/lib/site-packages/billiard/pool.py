# -*- coding: utf-8 -*-
#
# Module providing the `Pool` class for managing a process pool
#
# multiprocessing/pool.py
#
# Copyright (c) 2006-2008, R Oudkerk
# Licensed to PSF under a Contributor Agreement.
#
from __future__ import absolute_import
from __future__ import with_statement

#
# Imports
#

import collections
import errno
import itertools
import os
import platform
import signal
import sys
import threading
import time
import Queue
import warnings

from . import Event, Process, cpu_count
from . import util
from .common import pickle_loads, reset_signals, restart_state
from .compat import get_errno
from .einfo import ExceptionInfo
from .exceptions import (
    CoroStop,
    RestartFreqExceeded,
    SoftTimeLimitExceeded,
    Terminated,
    TimeLimitExceeded,
    TimeoutError,
    WorkerLostError,
)
from .util import Finalize, debug

if platform.system() == 'Windows':  # pragma: no cover
    # On Windows os.kill calls TerminateProcess which cannot be
    # handled by # any process, so this is needed to terminate the task
    # *and its children* (if any).
    from ._win import kill_processtree as _kill  # noqa
else:
    from os import kill as _kill                 # noqa


try:
    next = next
except NameError:
    def next(it, *args):  # noqa
        try:
            return it.next()
        except StopIteration:
            if not args:
                raise
            return args[0]

PY3 = sys.version_info[0] == 3

try:
    TIMEOUT_MAX = threading.TIMEOUT_MAX
except AttributeError:  # pragma: no cover
    TIMEOUT_MAX = 1e10  # noqa


if PY3:
    _Semaphore = threading.Semaphore
else:
    _Semaphore = threading._Semaphore  # noqa

#
# Constants representing the state of a pool
#

RUN = 0
CLOSE = 1
TERMINATE = 2

#
# Constants representing the state of a job
#

ACK = 0
READY = 1

#
# Exit code constants
#
EX_OK = 0
EX_FAILURE = 1
EX_RECYCLE = 0x9B


# Signal used for soft time limits.
SIG_SOFT_TIMEOUT = getattr(signal, "SIGUSR1", None)

#
# Miscellaneous
#

LOST_WORKER_TIMEOUT = 10.0
EX_OK = getattr(os, "EX_OK", 0)

job_counter = itertools.count()


def mapstar(args):
    return map(*args)


def starmapstar(args):
    return list(itertools.starmap(args[0], args[1]))


def error(msg, *args, **kwargs):
    if util._logger:
        util._logger.error(msg, *args, **kwargs)


def stop_if_not_current(thread, timeout=None):
    if thread is not threading.currentThread():
        thread.stop(timeout)


class LaxBoundedSemaphore(_Semaphore):
    """Semaphore that checks that # release is <= # acquires,
    but ignores if # releases >= value."""

    def __init__(self, value=1, verbose=None):
        if PY3:
            _Semaphore.__init__(self, value)
        else:
            _Semaphore.__init__(self, value, verbose)
        self._initial_value = value

    def grow(self):
        if PY3:
            cond = self._cond
        else:
            cond = self._Semaphore__cond
        with cond:
            self._initial_value += 1
            self._Semaphore__value += 1
            cond.notify()

    def shrink(self):
        self._initial_value -= 1
        self.acquire()

    if PY3:

        def release(self):
            cond = self._cond
            with cond:
                if self._value < self._initial_value:
                    self._value += 1
                    cond.notify_all()

        def clear(self):
            while self._value < self._initial_value:
                _Semaphore.release(self)
    else:

        def release(self):  # noqa
            cond = self._Semaphore__cond
            with cond:
                if self._Semaphore__value < self._initial_value:
                    self._Semaphore__value += 1
                    cond.notifyAll()

        def clear(self):  # noqa
            while self._Semaphore__value < self._initial_value:
                _Semaphore.release(self)

#
# Exceptions
#


class MaybeEncodingError(Exception):
    """Wraps possible unpickleable errors, so they can be
    safely sent through the socket."""

    def __init__(self, exc, value):
        self.exc = repr(exc)
        self.value = repr(value)
        super(MaybeEncodingError, self).__init__(self.exc, self.value)

    def __repr__(self):
        return "<MaybeEncodingError: %s>" % str(self)

    def __str__(self):
        return "Error sending result: '%r'. Reason: '%r'." % (
            self.value, self.exc)


class WorkersJoined(Exception):
    """All workers have terminated."""


def soft_timeout_sighandler(signum, frame):
    raise SoftTimeLimitExceeded()

#
# Code run by worker processes
#


def worker(inqueue, outqueue, initializer=None, initargs=(),
           maxtasks=None, sentinel=None):
    pid = os.getpid()
    assert maxtasks is None or (type(maxtasks) == int and maxtasks > 0)
    put = outqueue.put
    get = inqueue.get
    loads = pickle_loads

    if hasattr(inqueue, '_reader'):

        if hasattr(inqueue, 'get_payload') and inqueue.get_payload:
            get_payload = inqueue.get_payload

            def poll(timeout):
                if inqueue._reader.poll(timeout):
                    return True, loads(get_payload())
                return False, None
        else:
            def poll(timeout):
                if inqueue._reader.poll(timeout):
                    return True, get()
                return False, None
    else:

        def poll(timeout):  # noqa
            try:
                return True, get(timeout=timeout)
            except Queue.Empty:
                return False, None

    if hasattr(inqueue, '_writer'):
        inqueue._writer.close()
        outqueue._reader.close()

    if initializer is not None:
        initializer(*initargs)

    # Make sure all exiting signals call finally: blocks.
    # this is important for the semaphore to be released.
    reset_signals()

    # install signal handler for soft timeouts.
    if SIG_SOFT_TIMEOUT is not None:
        signal.signal(SIG_SOFT_TIMEOUT, soft_timeout_sighandler)

    try:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    except (AttributeError):
        pass

    exitcode = None
    completed = 0
    while maxtasks is None or (maxtasks and completed < maxtasks):
        if sentinel is not None and sentinel.is_set():
            debug('worker got sentinel -- exiting')
            exitcode = EX_OK
            break

        try:
            ready, task = poll(1.0)
            if not ready:
                continue
        except (EOFError, IOError), exc:
            if get_errno(exc) == errno.EINTR:
                continue  # interrupted, maybe by gdb
            debug('worker got EOFError or IOError -- exiting')
            exitcode = EX_FAILURE
            break

        if task is None:
            debug('worker got sentinel -- exiting')
            exitcode = EX_OK
            break

        job, i, func, args, kwds = task
        put((ACK, (job, i, time.time(), pid)))
        try:
            result = (True, func(*args, **kwds))
        except Exception:
            result = (False, ExceptionInfo())
        try:
            put((READY, (job, i, result)))
        except Exception, exc:
            _, _, tb = sys.exc_info()
            try:
                wrapped = MaybeEncodingError(exc, result[1])
                einfo = ExceptionInfo((MaybeEncodingError, wrapped, tb))
                put((READY, (job, i, (False, einfo))))
            finally:
                del(tb)

        completed += 1
    debug('worker exiting after %d tasks', completed)
    if exitcode is None and maxtasks:
        exitcode = EX_RECYCLE if completed == maxtasks else EX_FAILURE
    sys.exit(exitcode or EX_OK)

#
# Class representing a process pool
#


class PoolThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self._state = RUN
        self._was_started = False
        self.daemon = True

    def run(self):
        try:
            return self.body()
        except RestartFreqExceeded, exc:
            error("Thread %r crashed: %r", type(self).__name__, exc,
                  exc_info=True)
            _kill(os.getpid(), signal.SIGTERM)
            sys.exit()
        except Exception, exc:
            error("Thread %r crashed: %r", type(self).__name__, exc,
                  exc_info=True)
            os._exit(1)

    def start(self, *args, **kwargs):
        self._was_started = True
        super(PoolThread, self).start(*args, **kwargs)

    def on_stop_not_started(self):
        pass

    def stop(self, timeout=None):
        if self._was_started:
            self.join(timeout)
            return
        self.on_stop_not_started()

    def terminate(self):
        self._state = TERMINATE

    def close(self):
        self._state = CLOSE


class Supervisor(PoolThread):

    def __init__(self, pool):
        self.pool = pool
        super(Supervisor, self).__init__()

    def body(self):
        debug('worker handler starting')

        time.sleep(0.8)

        pool = self.pool

        try:
            # do a burst at startup to verify that we can start
            # our pool processes, and in that time we lower
            # the max restart frequency.
            prev_state = pool.restart_state
            pool.restart_state = restart_state(10 * pool._processes, 1)
            for _ in xrange(10):
                if self._state == RUN and pool._state == RUN:
                    pool._maintain_pool()
                    time.sleep(0.1)

            # Keep maintaing workers until the cache gets drained, unless
            # the pool is termianted
            pool.restart_state = prev_state
            while self._state == RUN and pool._state == RUN:
                pool._maintain_pool()
                time.sleep(0.8)
        except RestartFreqExceeded:
            pool.close()
            pool.join()
            raise
        debug('worker handler exiting')


class TaskHandler(PoolThread):

    def __init__(self, taskqueue, put, outqueue, pool):
        self.taskqueue = taskqueue
        self.put = put
        self.outqueue = outqueue
        self.pool = pool
        super(TaskHandler, self).__init__()

    def body(self):
        taskqueue = self.taskqueue
        put = self.put

        for taskseq, set_length in iter(taskqueue.get, None):
            try:
                i = -1
                for i, task in enumerate(taskseq):
                    if self._state:
                        debug('task handler found thread._state != RUN')
                        break
                    try:
                        put(task)
                    except IOError:
                        debug('could not put task on queue')
                        break
                else:
                    if set_length:
                        debug('doing set_length()')
                        set_length(i + 1)
                    continue
                break
            except Exception, exc:
                print("Task Handler ERROR: %r" % (exc, ))
                break
        else:
            debug('task handler got sentinel')

        self.tell_others()

    def tell_others(self):
        outqueue = self.outqueue
        put = self.put
        pool = self.pool

        try:
            # tell result handler to finish when cache is empty
            debug('task handler sending sentinel to result handler')
            outqueue.put(None)

            # tell workers there is no more work
            debug('task handler sending sentinel to workers')
            for p in pool:
                put(None)
        except IOError:
            debug('task handler got IOError when sending sentinels')

        debug('task handler exiting')

    def on_stop_not_started(self):
        self.tell_others()


class TimeoutHandler(PoolThread):

    def __init__(self, processes, cache, t_soft, t_hard):
        self.processes = processes
        self.cache = cache
        self.t_soft = t_soft
        self.t_hard = t_hard
        self._it = None
        super(TimeoutHandler, self).__init__()

    def _process_by_pid(self, pid):
        for index, process in enumerate(self.processes):
                if process.pid == pid:
                    return process, index
        return None, None

    def on_soft_timeout(self, job):
        debug('soft time limit exceeded for %r', job)
        process, _index = self._process_by_pid(job._worker_pid)
        if not process:
            return

        # Run timeout callback
        if job._timeout_callback is not None:
            job._timeout_callback(soft=True, timeout=job._soft_timeout)

        try:
            _kill(job._worker_pid, SIG_SOFT_TIMEOUT)
        except OSError, exc:
            if get_errno(exc) != errno.ESRCH:
                raise

    def on_hard_timeout(self, job):
        if job.ready():
            return
        debug('hard time limit exceeded for %r', job)
        # Remove from cache and set return value to an exception
        try:
            raise TimeLimitExceeded(job._timeout)
        except TimeLimitExceeded:
            job._set(job._job, (False, ExceptionInfo()))
        else:  # pragma: no cover
            pass

        # Remove from _pool
        process, _index = self._process_by_pid(job._worker_pid)

        # Run timeout callback
        if job._timeout_callback is not None:
            job._timeout_callback(soft=False, timeout=job._timeout)
        if process:
            self._trywaitkill(process)

    def _trywaitkill(self, worker):
        debug('timeout: sending TERM to %s', worker._name)
        try:
            worker.terminate()
        except OSError:
            pass
        else:
            if worker._popen.wait(timeout=0.1):
                return
        debug('timeout: TERM timed-out, now sending KILL to %s', worker._name)
        try:
            _kill(worker.pid, signal.SIGKILL)
        except OSError:
            pass

    def handle_timeouts(self):
        cache = self.cache
        t_hard, t_soft = self.t_hard, self.t_soft
        dirty = set()
        on_soft_timeout = self.on_soft_timeout
        on_hard_timeout = self.on_hard_timeout

        def _timed_out(start, timeout):
            if not start or not timeout:
                return False
            if time.time() >= start + timeout:
                return True

        # Inner-loop
        while self._state == RUN:

            # Remove dirty items not in cache anymore
            if dirty:
                dirty = set(k for k in dirty if k in cache)

            for i, job in cache.items():
                ack_time = job._time_accepted
                soft_timeout = job._soft_timeout
                if soft_timeout is None:
                    soft_timeout = t_soft
                hard_timeout = job._timeout
                if hard_timeout is None:
                    hard_timeout = t_hard
                if _timed_out(ack_time, hard_timeout):
                    on_hard_timeout(job)
                elif i not in dirty and _timed_out(ack_time, soft_timeout):
                    on_soft_timeout(job)
                    dirty.add(i)
            yield

    def body(self):
        while self._state == RUN:
            try:
                for _ in self.handle_timeouts():
                    time.sleep(1.0)  # don't spin
            except CoroStop:
                break
        debug('timeout handler exiting')

    def handle_event(self, *args):
        if self._it is None:
            self._it = self.handle_timeouts()
        try:
            self._it.next()
        except StopIteration:
            self._it = None


class ResultHandler(PoolThread):

    def __init__(self, outqueue, get, cache, poll,
                 join_exited_workers, putlock, restart_state, check_timeouts):
        self.outqueue = outqueue
        self.get = get
        self.cache = cache
        self.poll = poll
        self.join_exited_workers = join_exited_workers
        self.putlock = putlock
        self.restart_state = restart_state
        self._it = None
        self._shutdown_complete = False
        self.check_timeouts = check_timeouts
        super(ResultHandler, self).__init__()

    def on_stop_not_started(self):
        # used when pool started without result handler thread.
        self.finish_at_shutdown(handle_timeouts=True)

    def _process_result(self, timeout=1.0):
        cache = self.cache
        poll = self.poll
        putlock = self.putlock
        restart_state = self.restart_state

        def on_ack(job, i, time_accepted, pid):
            try:
                cache[job]._ack(i, time_accepted, pid)
            except (KeyError, AttributeError):
                # Object gone or doesn't support _ack (e.g. IMAPIterator).
                pass

        def on_ready(job, i, obj):
            restart_state.R = 0
            try:
                item = cache[job]
            except KeyError:
                return
            if not item.ready():
                if putlock is not None:
                    putlock.release()
            try:
                item._set(i, obj)
            except KeyError:
                pass

        state_handlers = {ACK: on_ack, READY: on_ready}

        def on_state_change(task):
            state, args = task
            try:
                state_handlers[state](*args)
            except KeyError:
                debug("Unknown job state: %s (args=%s)", state, args)

        while 1:
            try:
                ready, task = poll(timeout)
            except (IOError, EOFError), exc:
                debug('result handler got %r -- exiting', exc)
                raise CoroStop()

            if self._state:
                assert self._state == TERMINATE
                debug('result handler found thread._state=TERMINATE')
                raise CoroStop()

            if ready:
                if task is None:
                    debug('result handler got sentinel')
                    raise CoroStop()
                on_state_change(task)
                if timeout != 0:  # blocking
                    break
            else:
                break

        yield

    def handle_event(self, *args):
        if self._state == RUN:
            if self._it is None:
                self._it = self._process_result(0)  # non-blocking
            try:
                self._it.next()
            except (StopIteration, CoroStop):
                self._it = None

    def body(self):
        debug('result handler starting')
        try:
            while self._state == RUN:
                try:
                    for _ in self._process_result(1.0):  # blocking
                        pass
                except CoroStop:
                    break
        finally:
            self.finish_at_shutdown()

    def finish_at_shutdown(self, handle_timeouts=False):
        self._shutdown_complete = True
        get = self.get
        outqueue = self.outqueue
        cache = self.cache
        poll = self.poll
        join_exited_workers = self.join_exited_workers
        putlock = self.putlock
        restart_state = self.restart_state
        check_timeouts = self.check_timeouts

        def on_ack(job, i, time_accepted, pid):
            try:
                cache[job]._ack(i, time_accepted, pid)
            except (KeyError, AttributeError):
                # Object gone or doesn't support _ack (e.g. IMAPIterator).
                pass

        def on_ready(job, i, obj):
            restart_state.R = 0
            try:
                item = cache[job]
            except KeyError:
                return
            if not item.ready():
                if putlock is not None:
                    putlock.release()
            try:
                item._set(i, obj)
            except KeyError:
                pass

        state_handlers = {ACK: on_ack, READY: on_ready}

        def on_state_change(task):
            state, args = task
            try:
                state_handlers[state](*args)
            except KeyError:
                debug("Unknown job state: %s (args=%s)", state, args)

        time_terminate = None
        while cache and self._state != TERMINATE:
            if check_timeouts is not None:
                check_timeouts()
            try:
                ready, task = poll(1.0)
            except (IOError, EOFError), exc:
                debug('result handler got %r -- exiting', exc)
                return

            if ready:
                if task is None:
                    debug('result handler ignoring extra sentinel')
                    continue

                on_state_change(task)
            try:
                join_exited_workers(shutdown=True)
            except WorkersJoined:
                now = time.time()
                if not time_terminate:
                    time_terminate = now
                else:
                    if now - time_terminate > 5.0:
                        debug('result handler exiting: timed out')
                        break
                    debug('result handler: all workers terminated, '
                          'timeout in %ss',
                          abs(min(now - time_terminate - 5.0, 0)))

        if hasattr(outqueue, '_reader'):
            debug('ensuring that outqueue is not full')
            # If we don't make room available in outqueue then
            # attempts to add the sentinel (None) to outqueue may
            # block.  There is guaranteed to be no more than 2 sentinels.
            try:
                for i in range(10):
                    if not outqueue._reader.poll():
                        break
                    get()
            except (IOError, EOFError):
                pass

        debug('result handler exiting: len(cache)=%s, thread._state=%s',
              len(cache), self._state)


class Pool(object):
    '''
    Class which supports an async version of applying functions to arguments.
    '''
    Process = Process
    Supervisor = Supervisor
    TaskHandler = TaskHandler
    TimeoutHandler = TimeoutHandler
    ResultHandler = ResultHandler
    SoftTimeLimitExceeded = SoftTimeLimitExceeded

    def __init__(self, processes=None, initializer=None, initargs=(),
                 maxtasksperchild=None, timeout=None, soft_timeout=None,
                 lost_worker_timeout=LOST_WORKER_TIMEOUT,
                 max_restarts=None, max_restart_freq=1,
                 on_process_up=None,
                 on_process_down=None,
                 on_timeout_set=None,
                 on_timeout_cancel=None,
                 threads=True,
                 semaphore=None,
                 putlocks=False,
                 allow_restart=False):
        self._setup_queues()
        self._taskqueue = Queue.Queue()
        self._cache = {}
        self._state = RUN
        self.timeout = timeout
        self.soft_timeout = soft_timeout
        self._maxtasksperchild = maxtasksperchild
        self._initializer = initializer
        self._initargs = initargs
        self.lost_worker_timeout = lost_worker_timeout or LOST_WORKER_TIMEOUT
        self.on_process_up = on_process_up
        self.on_process_down = on_process_down
        self.on_timeout_set = on_timeout_set
        self.on_timeout_cancel = on_timeout_cancel
        self.threads = threads
        self.readers = {}
        self.allow_restart = allow_restart
        # Contains processes that we have terminated,
        # and that the supervisor should not raise an error for.
        self.signalled = set()

        if soft_timeout and SIG_SOFT_TIMEOUT is None:
            warnings.warn(UserWarning(
                "Soft timeouts are not supported: "
                "on this platform: It does not have the SIGUSR1 signal.",
            ))
            soft_timeout = None

        if processes is None:
            try:
                processes = cpu_count()
            except NotImplementedError:
                processes = 1
        self._processes = processes
        self.max_restarts = max_restarts or round(processes * 100)
        self.restart_state = restart_state(max_restarts, max_restart_freq or 1)

        if initializer is not None and not callable(initializer):
            raise TypeError('initializer must be a callable')

        self._pool = []
        self._poolctrl = {}
        self.putlocks = putlocks
        self._putlock = semaphore or LaxBoundedSemaphore(self._processes)
        for i in range(processes):
            self._create_worker_process(i)

        self._worker_handler = self.Supervisor(self)
        if threads:
            self._worker_handler.start()
        else:
            self.readers.update(
                dict((w._popen.sentinel, self.maintain_pool)
                     for w in self._pool))

        self._task_handler = self.TaskHandler(self._taskqueue,
                                              self._quick_put,
                                              self._outqueue,
                                              self._pool)
        if threads:
            self._task_handler.start()

        # Thread killing timedout jobs.
        self._timeout_handler = self.TimeoutHandler(
            self._pool, self._cache,
            self.soft_timeout, self.timeout,
        )
        self._timeout_handler_mutex = threading.Lock()
        self._timeout_handler_started = False
        if self.timeout is not None or self.soft_timeout is not None:
            self._start_timeout_handler()

        # If running without threads, we need to check for timeouts
        # while waiting for unfinished work at shutdown.
        check_timeouts = None
        if not threads:
            check_timeouts = self._timeout_handler.handle_event

        # Thread processing results in the outqueue.
        self._result_handler = self.ResultHandler(
            self._outqueue, self._quick_get, self._cache,
            self._poll_result, self._join_exited_workers,
            self._putlock, self.restart_state, check_timeouts,
        )

        if threads:
            self._result_handler.start()
        else:
            self.readers[self._outqueue._reader] = \
                self._result_handler.handle_event

        self._terminate = Finalize(
            self, self._terminate_pool,
            args=(self._taskqueue, self._inqueue, self._outqueue,
                  self._pool, self._worker_handler, self._task_handler,
                  self._result_handler, self._cache,
                  self._timeout_handler),
            exitpriority=15,
        )

    def _create_worker_process(self, i):
        sentinel = Event() if self.allow_restart else None
        w = self.Process(
            target=worker,
            args=(
                self._inqueue, self._outqueue,
                self._initializer, self._initargs,
                self._maxtasksperchild,
                sentinel
            ),
        )
        self._pool.append(w)
        w.name = w.name.replace('Process', 'PoolWorker')
        w.daemon = True
        w.index = i
        w.start()
        if self.on_process_up:
            self.on_process_up(w)
        self._poolctrl[w.pid] = sentinel
        return w

    def _join_exited_workers(self, shutdown=False):
        """Cleanup after any worker processes which have exited due to
        reaching their specified lifetime. Returns True if any workers were
        cleaned up.
        """
        now = None
        # The worker may have published a result before being terminated,
        # but we have no way to accurately tell if it did.  So we wait for
        # _lost_worker_timeout seconds before we mark the job with
        # WorkerLostError.
        for job in [job for job in self._cache.values()
                    if not job.ready() and job._worker_lost]:
            now = now or time.time()
            lost_time, lost_ret = job._worker_lost
            if now - lost_time > job._lost_worker_timeout:
                try:
                    raise WorkerLostError(
                        "Worker exited prematurely (exitcode: %r)." % (
                            lost_ret, ))
                except WorkerLostError:
                    exc_info = ExceptionInfo()
                    job._set(None, (False, exc_info))
                else:  # pragma: no cover
                    pass

        if shutdown and not len(self._pool):
            raise WorkersJoined()

        cleaned, exitcodes = {}, {}
        for i in reversed(range(len(self._pool))):
            worker = self._pool[i]
            if worker.exitcode is not None:
                # worker exited
                debug('Supervisor: cleaning up worker %d', i)
                worker.join()
                debug('Supervisor: worked %d joined', i)
                cleaned[worker.pid] = worker
                exitcodes[worker.pid] = worker.exitcode
                if worker.exitcode not in (EX_OK, EX_RECYCLE):
                    error('Process %r pid:%r exited with exitcode %r' % (
                        worker.name, worker.pid, worker.exitcode))
                del self._pool[i]
                del self._poolctrl[worker.pid]
        if cleaned:
            for job in self._cache.values():
                for worker_pid in job.worker_pids():
                    if worker_pid in cleaned and not job.ready():
                        if worker_pid in self.signalled:
                            try:
                                raise Terminated(-exitcodes[worker_pid])
                            except Terminated:
                                job._set(None, (False, ExceptionInfo()))
                        else:
                            job._worker_lost = (time.time(),
                                                exitcodes[worker_pid])
                        break
            for worker in cleaned.itervalues():
                if self.on_process_down:
                    self.on_process_down(worker)
            return exitcodes.values()
        return []

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return self.terminate()

    def shrink(self, n=1):
        for i, worker in enumerate(self._iterinactive()):
            self._processes -= 1
            if self._putlock:
                self._putlock.shrink()
            worker.terminate()
            if i == n - 1:
                return
        raise ValueError("Can't shrink pool. All processes busy!")

    def grow(self, n=1):
        for i in xrange(n):
            #assert len(self._pool) == self._processes
            self._processes += 1
            if self._putlock:
                self._putlock.grow()

    def _iterinactive(self):
        for worker in self._pool:
            if not self._worker_active(worker):
                yield worker
        raise StopIteration()

    def _worker_active(self, worker):
        for job in self._cache.values():
            if worker.pid in job.worker_pids():
                return True
        return False

    def _repopulate_pool(self, exitcodes):
        """Bring the number of pool processes up to the specified number,
        for use after reaping workers which have exited.
        """
        for i in range(self._processes - len(self._pool)):
            if self._state != RUN:
                return
            try:
                if exitcodes and exitcodes[i] not in (EX_OK, EX_RECYCLE):
                    self.restart_state.step()
            except IndexError:
                self.restart_state.step()
            self._create_worker_process(self._avail_index())
            debug('added worker')

    def _avail_index(self):
        assert len(self._pool) < self._processes
        indices = set(p.index for p in self._pool)
        return next(i for i in range(self._processes) if i not in indices)

    def did_start_ok(self):
        return not self._join_exited_workers()

    def _maintain_pool(self):
        """"Clean up any exited workers and start replacements for them.
        """
        joined = self._join_exited_workers()
        self._repopulate_pool(joined)
        for i in range(len(joined)):
            if self._putlock is not None:
                self._putlock.release()

    def maintain_pool(self, *args, **kwargs):
        if self._worker_handler._state == RUN and self._state == RUN:
            try:
                self._maintain_pool()
            except RestartFreqExceeded:
                self.close()
                self.join()
                raise

    def _setup_queues(self):
        from billiard.queues import SimpleQueue
        self._inqueue = SimpleQueue()
        self._outqueue = SimpleQueue()
        self._quick_put = self._inqueue._writer.send
        self._quick_get = self._outqueue._reader.recv

        def _poll_result(timeout):
            if self._outqueue._reader.poll(timeout):
                return True, self._quick_get()
            return False, None
        self._poll_result = _poll_result

    def _start_timeout_handler(self):
        # ensure more than one thread does not start the timeout handler
        # thread at once.
        if self.threads:
            with self._timeout_handler_mutex:
                if not self._timeout_handler_started:
                    self._timeout_handler_started = True
                    self._timeout_handler.start()

    def apply(self, func, args=(), kwds={}):
        '''
        Equivalent of `func(*args, **kwargs)`.
        '''
        if self._state == RUN:
            return self.apply_async(func, args, kwds).get()

    def starmap(self, func, iterable, chunksize=None):
        '''
        Like `map()` method but the elements of the `iterable` are expected to
        be iterables as well and will be unpacked as arguments. Hence
        `func` and (a, b) becomes func(a, b).
        '''
        if self._state == RUN:
            return self._map_async(func, iterable,
                                   starmapstar, chunksize).get()

    def starmap_async(self, func, iterable, chunksize=None,
                      callback=None, error_callback=None):
        '''
        Asynchronous version of `starmap()` method.
        '''
        if self._state == RUN:
            return self._map_async(func, iterable, starmapstar, chunksize,
                                   callback, error_callback)

    def map(self, func, iterable, chunksize=None):
        '''
        Apply `func` to each element in `iterable`, collecting the results
        in a list that is returned.
        '''
        if self._state == RUN:
            return self.map_async(func, iterable, chunksize).get()

    def imap(self, func, iterable, chunksize=1, lost_worker_timeout=None):
        '''
        Equivalent of `map()` -- can be MUCH slower than `Pool.map()`.
        '''
        if self._state != RUN:
            return
        lost_worker_timeout = lost_worker_timeout or self.lost_worker_timeout
        if chunksize == 1:
            result = IMapIterator(self._cache,
                                  lost_worker_timeout=lost_worker_timeout)
            self._taskqueue.put((
                ((result._job, i, func, (x,), {})
                 for i, x in enumerate(iterable)),
                result._set_length,
            ))
            return result
        else:
            assert chunksize > 1
            task_batches = Pool._get_tasks(func, iterable, chunksize)
            result = IMapIterator(self._cache,
                                  lost_worker_timeout=lost_worker_timeout)
            self._taskqueue.put((
                ((result._job, i, mapstar, (x,), {})
                 for i, x in enumerate(task_batches)),
                result._set_length,
            ))
            return (item for chunk in result for item in chunk)

    def imap_unordered(self, func, iterable, chunksize=1,
                       lost_worker_timeout=None):
        '''
        Like `imap()` method but ordering of results is arbitrary.
        '''
        if self._state != RUN:
            return
        lost_worker_timeout = lost_worker_timeout or self.lost_worker_timeout
        if chunksize == 1:
            result = IMapUnorderedIterator(
                self._cache, lost_worker_timeout=lost_worker_timeout,
            )
            self._taskqueue.put((
                ((result._job, i, func, (x,), {})
                 for i, x in enumerate(iterable)),
                result._set_length,
            ))
            return result
        else:
            assert chunksize > 1
            task_batches = Pool._get_tasks(func, iterable, chunksize)
            result = IMapUnorderedIterator(
                self._cache, lost_worker_timeout=lost_worker_timeout,
            )
            self._taskqueue.put((
                ((result._job, i, mapstar, (x,), {})
                 for i, x in enumerate(task_batches)),
                result._set_length,
            ))
            return (item for chunk in result for item in chunk)

    def apply_async(self, func, args=(), kwds={},
                    callback=None, error_callback=None, accept_callback=None,
                    timeout_callback=None, waitforslot=None,
                    soft_timeout=None, timeout=None, lost_worker_timeout=None,
                    callbacks_propagate=()):
        '''
        Asynchronous equivalent of `apply()` method.

        Callback is called when the functions return value is ready.
        The accept callback is called when the job is accepted to be executed.

        Simplified the flow is like this:

            >>> if accept_callback:
            ...     accept_callback()
            >>> retval = func(*args, **kwds)
            >>> if callback:
            ...     callback(retval)

        '''
        if self._state != RUN:
            return
        soft_timeout = soft_timeout or self.soft_timeout
        timeout = timeout or self.timeout
        lost_worker_timeout = lost_worker_timeout or self.lost_worker_timeout
        if soft_timeout and SIG_SOFT_TIMEOUT is None:
            warnings.warn(UserWarning(
                "Soft timeouts are not supported: "
                "on this platform: It does not have the SIGUSR1 signal.",
            ))
            soft_timeout = None
        if waitforslot is None:
            waitforslot = self.putlocks
        if waitforslot and self._putlock is not None and self._state == RUN:
            self._putlock.acquire()
        if self._state == RUN:
            result = ApplyResult(
                self._cache, callback, accept_callback, timeout_callback,
                error_callback, soft_timeout, timeout, lost_worker_timeout,
                on_timeout_set=self.on_timeout_set,
                on_timeout_cancel=self.on_timeout_cancel,
                callbacks_propagate=callbacks_propagate,
            )
            if timeout or soft_timeout:
                # start the timeout handler thread when required.
                self._start_timeout_handler()
            if self.threads:
                self._taskqueue.put(([(result._job, None,
                                    func, args, kwds)], None))
            else:
                self._quick_put((result._job, None, func, args, kwds))
            return result

    def terminate_job(self, pid, sig=None):
        try:
            _kill(pid, sig or signal.SIGTERM)
        except OSError, exc:
            if get_errno(exc) != errno.ESRCH:
                raise
        else:
            self.signalled.add(pid)

    def map_async(self, func, iterable, chunksize=None,
                  callback=None, error_callback=None):
        '''
        Asynchronous equivalent of `map()` method.
        '''
        return self._map_async(
            func, iterable, mapstar, chunksize, callback, error_callback,
        )

    def _map_async(self, func, iterable, mapper, chunksize=None,
                   callback=None, error_callback=None):
        '''
        Helper function to implement map, starmap and their async counterparts.
        '''
        if self._state != RUN:
            return
        if not hasattr(iterable, '__len__'):
            iterable = list(iterable)

        if chunksize is None:
            chunksize, extra = divmod(len(iterable), len(self._pool) * 4)
            if extra:
                chunksize += 1
        if len(iterable) == 0:
            chunksize = 0

        task_batches = Pool._get_tasks(func, iterable, chunksize)
        result = MapResult(self._cache, chunksize, len(iterable), callback,
                           error_callback=error_callback)
        self._taskqueue.put((((result._job, i, mapper, (x,), {})
                              for i, x in enumerate(task_batches)), None))
        return result

    @staticmethod
    def _get_tasks(func, it, size):
        it = iter(it)
        while 1:
            x = tuple(itertools.islice(it, size))
            if not x:
                return
            yield (func, x)

    def __reduce__(self):
        raise NotImplementedError(
            'pool objects cannot be passed between processes or pickled',
        )

    def close(self):
        debug('closing pool')
        if self._state == RUN:
            self._state = CLOSE
            if self._putlock:
                self._putlock.clear()
            self._worker_handler.close()
            self._taskqueue.put(None)
            stop_if_not_current(self._worker_handler)

    def terminate(self):
        debug('terminating pool')
        self._state = TERMINATE
        self._worker_handler.terminate()
        self._terminate()

    def join(self):
        assert self._state in (CLOSE, TERMINATE)
        debug('joining worker handler')
        stop_if_not_current(self._worker_handler)
        debug('joining task handler')
        stop_if_not_current(self._task_handler)
        debug('joining result handler')
        stop_if_not_current(self._result_handler)
        debug('result handler joined')
        for i, p in enumerate(self._pool):
            debug('joining worker %s/%s (%r)', i, len(self._pool), p)
            p.join()

    def restart(self):
        for e in self._poolctrl.itervalues():
            e.set()

    @staticmethod
    def _help_stuff_finish(inqueue, task_handler, size):
        # task_handler may be blocked trying to put items on inqueue
        debug('removing tasks from inqueue until task handler finished')
        inqueue._rlock.acquire()
        while task_handler.is_alive() and inqueue._reader.poll():
            inqueue._reader.recv()
            time.sleep(0)

    @classmethod
    def _terminate_pool(cls, taskqueue, inqueue, outqueue, pool,
                        worker_handler, task_handler,
                        result_handler, cache, timeout_handler):

        # this is guaranteed to only be called once
        debug('finalizing pool')

        worker_handler.terminate()

        task_handler.terminate()
        taskqueue.put(None)                 # sentinel

        debug('helping task handler/workers to finish')
        cls._help_stuff_finish(inqueue, task_handler, len(pool))

        result_handler.terminate()
        outqueue.put(None)                  # sentinel

        if timeout_handler is not None:
            timeout_handler.terminate()

        # Terminate workers which haven't already finished
        if pool and hasattr(pool[0], 'terminate'):
            debug('terminating workers')
            for p in pool:
                if p.exitcode is None:
                    p.terminate()

        debug('joining task handler')
        task_handler.stop()

        debug('joining result handler')
        result_handler.stop()

        if timeout_handler is not None:
            debug('joining timeout handler')
            timeout_handler.stop(TIMEOUT_MAX)

        if pool and hasattr(pool[0], 'terminate'):
            debug('joining pool workers')
            for p in pool:
                if p.is_alive():
                    # worker has not yet exited
                    debug('cleaning up worker %d', p.pid)
                    p.join()
            debug('pool workers joined')
DynamicPool = Pool

#
# Class whose instances are returned by `Pool.apply_async()`
#


class ApplyResult(object):
    _worker_lost = None

    def __init__(self, cache, callback, accept_callback=None,
                 timeout_callback=None, error_callback=None, soft_timeout=None,
                 timeout=None, lost_worker_timeout=LOST_WORKER_TIMEOUT,
                 on_timeout_set=None, on_timeout_cancel=None,
                 callbacks_propagate=()):
        self._mutex = threading.Lock()
        self._event = threading.Event()
        self._job = job_counter.next()
        self._cache = cache
        self._callback = callback
        self._accept_callback = accept_callback
        self._error_callback = error_callback
        self._timeout_callback = timeout_callback
        self._timeout = timeout
        self._soft_timeout = soft_timeout
        self._lost_worker_timeout = lost_worker_timeout
        self._on_timeout_set = on_timeout_set
        self._on_timeout_cancel = on_timeout_cancel
        self._callbacks_propagate = callbacks_propagate or ()

        self._accepted = False
        self._worker_pid = None
        self._time_accepted = None
        cache[self._job] = self

    def ready(self):
        return self._event.isSet()

    def accepted(self):
        return self._accepted

    def successful(self):
        assert self.ready()
        return self._success

    def worker_pids(self):
        return filter(None, [self._worker_pid])

    def wait(self, timeout=None):
        self._event.wait(timeout)

    def get(self, timeout=None):
        self.wait(timeout)
        if not self.ready():
            raise TimeoutError
        if self._success:
            return self._value
        else:
            raise self._value.exception

    def safe_apply_callback(self, fun, *args):
        if fun:
            try:
                fun(*args)
            except self._callbacks_propagate:
                raise
            except Exception, exc:
                error("Pool callback raised exception: %r", exc,
                      exc_info=True)

    def _set(self, i, obj):
        with self._mutex:
            if self._on_timeout_cancel:
                self._on_timeout_cancel(self)
            self._success, self._value = obj
            self._event.set()
            if self._accepted:
                self._cache.pop(self._job, None)

            # apply callbacks last
            if self._callback and self._success:
                self.safe_apply_callback(
                    self._callback, self._value)
            if (self._value is not None and
                    self._error_callback and not self._success):
                self.safe_apply_callback(
                    self._error_callback, self._value)

    def _ack(self, i, time_accepted, pid):
        with self._mutex:
            self._accepted = True
            self._time_accepted = time_accepted
            self._worker_pid = pid
            if self.ready():
                self._cache.pop(self._job, None)
            if self._on_timeout_set:
                self._on_timeout_set(self, self._soft_timeout, self._timeout)
            if self._accept_callback:
                self.safe_apply_callback(
                    self._accept_callback, pid, time_accepted)

#
# Class whose instances are returned by `Pool.map_async()`
#


class MapResult(ApplyResult):

    def __init__(self, cache, chunksize, length, callback, error_callback):
        ApplyResult.__init__(
            self, cache, callback, error_callback=error_callback,
        )
        self._success = True
        self._length = length
        self._value = [None] * length
        self._accepted = [False] * length
        self._worker_pid = [None] * length
        self._time_accepted = [None] * length
        self._chunksize = chunksize
        if chunksize <= 0:
            self._number_left = 0
            self._event.set()
            del cache[self._job]
        else:
            self._number_left = length // chunksize + bool(length % chunksize)

    def _set(self, i, success_result):
        success, result = success_result
        if success:
            self._value[i * self._chunksize:(i + 1) * self._chunksize] = result
            self._number_left -= 1
            if self._number_left == 0:
                if self._callback:
                    self._callback(self._value)
                if self._accepted:
                    self._cache.pop(self._job, None)
                self._event.set()
        else:
            self._success = False
            self._value = result
            if self._error_callback:
                self._error_callback(self._value)
            if self._accepted:
                self._cache.pop(self._job, None)
            self._event.set()

    def _ack(self, i, time_accepted, pid):
        start = i * self._chunksize
        stop = (i + 1) * self._chunksize
        for j in range(start, stop):
            self._accepted[j] = True
            self._worker_pid[j] = pid
            self._time_accepted[j] = time_accepted
        if self.ready():
            self._cache.pop(self._job, None)

    def accepted(self):
        return all(self._accepted)

    def worker_pids(self):
        return filter(None, self._worker_pid)

#
# Class whose instances are returned by `Pool.imap()`
#


class IMapIterator(object):
    _worker_lost = None

    def __init__(self, cache, lost_worker_timeout=LOST_WORKER_TIMEOUT):
        self._cond = threading.Condition(threading.Lock())
        self._job = job_counter.next()
        self._cache = cache
        self._items = collections.deque()
        self._index = 0
        self._length = None
        self._ready = False
        self._unsorted = {}
        self._worker_pids = []
        self._lost_worker_timeout = lost_worker_timeout
        cache[self._job] = self

    def __iter__(self):
        return self

    def next(self, timeout=None):
        with self._cond:
            try:
                item = self._items.popleft()
            except IndexError:
                if self._index == self._length:
                    self._ready = True
                    raise StopIteration
                self._cond.wait(timeout)
                try:
                    item = self._items.popleft()
                except IndexError:
                    if self._index == self._length:
                        self._ready = True
                        raise StopIteration
                    raise TimeoutError

        success, value = item
        if success:
            return value
        raise Exception(value)

    __next__ = next                    # XXX

    def _set(self, i, obj):
        with self._cond:
            if self._index == i:
                self._items.append(obj)
                self._index += 1
                while self._index in self._unsorted:
                    obj = self._unsorted.pop(self._index)
                    self._items.append(obj)
                    self._index += 1
                self._cond.notify()
            else:
                self._unsorted[i] = obj

            if self._index == self._length:
                self._ready = True
                del self._cache[self._job]

    def _set_length(self, length):
        with self._cond:
            self._length = length
            if self._index == self._length:
                self._ready = True
                self._cond.notify()
                del self._cache[self._job]

    def _ack(self, i, time_accepted, pid):
        self._worker_pids.append(pid)

    def ready(self):
        return self._ready

    def worker_pids(self):
        return self._worker_pids

#
# Class whose instances are returned by `Pool.imap_unordered()`
#


class IMapUnorderedIterator(IMapIterator):

    def _set(self, i, obj):
        with self._cond:
            self._items.append(obj)
            self._index += 1
            self._cond.notify()
            if self._index == self._length:
                self._ready = True
                del self._cache[self._job]

#
#
#


class ThreadPool(Pool):

    from billiard.dummy import Process as DummyProcess
    Process = DummyProcess

    def __init__(self, processes=None, initializer=None, initargs=()):
        Pool.__init__(self, processes, initializer, initargs)

    def _setup_queues(self):
        self._inqueue = Queue.Queue()
        self._outqueue = Queue.Queue()
        self._quick_put = self._inqueue.put
        self._quick_get = self._outqueue.get

        def _poll_result(timeout):
            try:
                return True, self._quick_get(timeout=timeout)
            except Queue.Empty:
                return False, None
        self._poll_result = _poll_result

    @staticmethod
    def _help_stuff_finish(inqueue, task_handler, size):
        # put sentinels at head of inqueue to make workers finish
        with inqueue.not_empty:
            inqueue.queue.clear()
            inqueue.queue.extend([None] * size)
            inqueue.not_empty.notify_all()
