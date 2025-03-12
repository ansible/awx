# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Production settings for AWX project.

import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SQL_DEBUG = DEBUG

# Clear database settings to force production environment to define them.
DATABASES = {}

# Clear the secret key to force production environment to define it.
SECRET_KEY = None

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Ansible base virtualenv paths and enablement
# only used for deprecated fields and management commands for them
BASE_VENV_PATH = os.path.realpath("/var/lib/awx/venv")

# Very important that this is editable (not read_only) in the API
AWX_ISOLATION_SHOW_PATHS = [
    '/etc/pki/ca-trust:/etc/pki/ca-trust:O',
    '/usr/share/pki:/usr/share/pki:O',
]
