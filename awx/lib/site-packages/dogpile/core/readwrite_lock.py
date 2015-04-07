from .util import threading

import logging
log = logging.getLogger(__name__)

class LockError(Exception):
    pass

class ReadWriteMutex(object):
    """A mutex which allows multiple readers, single writer.
    
    :class:`.ReadWriteMutex` uses a Python ``threading.Condition``
    to provide this functionality across threads within a process.
    
    The Beaker package also contained a file-lock based version
    of this concept, so that readers/writers could be synchronized
    across processes with a common filesystem.  A future Dogpile 
    release may include this additional class at some point.
    
    """

    def __init__(self):
        # counts how many asynchronous methods are executing
        self.async = 0

        # pointer to thread that is the current sync operation
        self.current_sync_operation = None

        # condition object to lock on
        self.condition = threading.Condition(threading.Lock())

    def acquire_read_lock(self, wait = True):
        """Acquire the 'read' lock."""
        self.condition.acquire()
        try:
            # see if a synchronous operation is waiting to start
            # or is already running, in which case we wait (or just
            # give up and return)
            if wait:
                while self.current_sync_operation is not None:
                    self.condition.wait()
            else:
                if self.current_sync_operation is not None:
                    return False

            self.async += 1
            log.debug("%s acquired read lock", self)
        finally:
            self.condition.release()

        if not wait: 
            return True

    def release_read_lock(self):
        """Release the 'read' lock."""
        self.condition.acquire()
        try:
            self.async -= 1

            # check if we are the last asynchronous reader thread 
            # out the door.
            if self.async == 0:
                # yes. so if a sync operation is waiting, notifyAll to wake
                # it up
                if self.current_sync_operation is not None:
                    self.condition.notifyAll()
            elif self.async < 0:
                raise LockError("Synchronizer error - too many "
                                "release_read_locks called")
            log.debug("%s released read lock", self)
        finally:
            self.condition.release()

    def acquire_write_lock(self, wait = True):
        """Acquire the 'write' lock."""
        self.condition.acquire()
        try:
            # here, we are not a synchronous reader, and after returning,
            # assuming waiting or immediate availability, we will be.

            if wait:
                # if another sync is working, wait
                while self.current_sync_operation is not None:
                    self.condition.wait()
            else:
                # if another sync is working,
                # we dont want to wait, so forget it
                if self.current_sync_operation is not None:
                    return False

            # establish ourselves as the current sync 
            # this indicates to other read/write operations
            # that they should wait until this is None again
            self.current_sync_operation = threading.currentThread()

            # now wait again for asyncs to finish
            if self.async > 0:
                if wait:
                    # wait
                    self.condition.wait()
                else:
                    # we dont want to wait, so forget it
                    self.current_sync_operation = None
                    return False
            log.debug("%s acquired write lock", self)
        finally:
            self.condition.release()

        if not wait: 
            return True

    def release_write_lock(self):
        """Release the 'write' lock."""
        self.condition.acquire()
        try:
            if self.current_sync_operation is not threading.currentThread():
                raise LockError("Synchronizer error - current thread doesn't "
                                "have the write lock")

            # reset the current sync operation so 
            # another can get it
            self.current_sync_operation = None

            # tell everyone to get ready
            self.condition.notifyAll()

            log.debug("%s released write lock", self)
        finally:
            # everyone go !!
            self.condition.release()
