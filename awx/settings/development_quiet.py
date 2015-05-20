# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Development settings for AWX project, but with DEBUG disabled

# Load development settings.
from defaults import *  # NOQA

# Load development settings.
from development import *  # NOQA

# Disable capturing DEBUG
DEBUG = False
TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG
