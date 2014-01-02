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
