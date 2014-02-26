# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Development settings for AWX project.

# Python
import sys
import traceback

# Django Split Settings
from split_settings.tools import optional, include

# Load default settings.
from defaults import *

# Disable capturing all SQL queries when running celeryd in development.
if 'celeryd' in sys.argv:
    SQL_DEBUG = False

# Use a different callback consumer/queue for development, to avoid a conflict
# if there is also a nightly install running on the development machine.
CALLBACK_CONSUMER_PORT = "tcp://127.0.0.1:5557"
CALLBACK_QUEUE_PORT = "ipc:///tmp/callback_receiver_dev.ipc"

# If any local_*.py files are present in awx/settings/, use them to override
# default settings for development.  If not present, we can still run using
# only the defaults.
try:
    include(
        optional('local_*.py'),
        scope=locals(),
    )
except ImportError:
    traceback.print_exc()
    sys.exit(1)
