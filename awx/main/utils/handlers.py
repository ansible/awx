# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import logging
import os.path

# Django
from django.conf import settings
from django.utils.timezone import now

# AWX
from awx.main.exceptions import PostRunError


class RSysLogHandler(logging.handlers.SysLogHandler):

    append_nul = False

    def _connect_unixsocket(self, address):
        super(RSysLogHandler, self)._connect_unixsocket(address)
        self.socket.setblocking(False)

    def emit(self, msg):
        if not settings.LOG_AGGREGATOR_ENABLED:
            return
        if not os.path.exists(settings.LOGGING['handlers']['external_logger']['address']):
            return
        try:
            return super(RSysLogHandler, self).emit(msg)
        except ConnectionRefusedError:
            # rsyslogd has gone to lunch; this generally means that it's just
            # been restarted (due to a configuration change)
            # unfortunately, we can't log that because...rsyslogd is down (and
            # would just us back ddown this code path)
            pass
        except BlockingIOError:
            # for <some reason>, rsyslogd is no longer reading from the domain socket, and
            # we're unable to write any more to it without blocking (we've seen this behavior
            # from time to time when logging is totally misconfigured;
            # in this scenario, it also makes more sense to just drop the messages,
            # because the alternative is blocking the socket.send() in the
            # Python process, which we definitely don't want to do)
            pass


class SpecialInventoryHandler(logging.Handler):
    """Logging handler used for the saving-to-database part of inventory updates
    ran by the task system
    this dispatches events directly to be processed by the callback receiver,
    as opposed to ansible-runner
    """

    def __init__(self, event_handler, cancel_callback, job_timeout, verbosity,
                 start_time=None, counter=0, initial_line=0, **kwargs):
        self.event_handler = event_handler
        self.cancel_callback = cancel_callback
        self.job_timeout = job_timeout
        if start_time is None:
            self.job_start = now()
        else:
            self.job_start = start_time
        self.last_check = self.job_start
        self.counter = counter
        self.skip_level = [logging.WARNING, logging.INFO, logging.DEBUG, 0][verbosity]
        self._current_line = initial_line
        super(SpecialInventoryHandler, self).__init__(**kwargs)

    def emit(self, record):
        # check cancel and timeout status regardless of log level
        this_time = now()
        if (this_time - self.last_check).total_seconds() > 0.5:  # cancel callback is expensive
            self.last_check = this_time
            if self.cancel_callback():
                raise PostRunError('Inventory update has been canceled', status='canceled')
        if self.job_timeout and ((this_time - self.job_start).total_seconds() > self.job_timeout):
            raise PostRunError('Inventory update has timed out', status='canceled')

        # skip logging for low severity logs
        if record.levelno < self.skip_level:
            return

        self.counter += 1
        msg = self.format(record)
        n_lines = len(msg.strip().split('\n'))  # don't count line breaks at boundry of text
        dispatch_data = dict(
            created=now().isoformat(),
            event='verbose',
            counter=self.counter,
            stdout=msg,
            start_line=self._current_line,
            end_line=self._current_line + n_lines
        )
        self._current_line += n_lines

        self.event_handler(dispatch_data)


ColorHandler = logging.StreamHandler

if settings.COLOR_LOGS is True:
    try:
        from logutils.colorize import ColorizingStreamHandler

        class ColorHandler(ColorizingStreamHandler):

            def format(self, record):
                message = logging.StreamHandler.format(self, record)
                return '\n'.join([
                    self.colorize(line, record)
                    for line in message.splitlines()
                ])

            level_map = {
                logging.DEBUG: (None, 'green', True),
                logging.INFO: (None, None, True),
                logging.WARNING: (None, 'yellow', True),
                logging.ERROR: (None, 'red', True),
                logging.CRITICAL: (None, 'red', True),
            }
    except ImportError:
        # logutils is only used for colored logs in the dev environment
        pass
