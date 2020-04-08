# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import logging
import os.path

# Django
from django.conf import settings


class RSysLogHandler(logging.handlers.SysLogHandler):

    append_nul = False

    def emit(self, msg):
        if not settings.LOG_AGGREGATOR_ENABLED:
            return
        if not os.path.exists(settings.LOGGING['handlers']['external_logger']['address']):
            return
        return super(RSysLogHandler, self).emit(msg)


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
