# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

# Local Django settings for AWX project.  Rename to "local_settings.py" and
# edit as needed for your development environment.

# All variables defined in awx/settings/development.py will already be loaded
# into the global namespace before this file is loaded, to allow for reading
# and updating the default settings as needed.

###############################################################################
# MISC PROJECT SETTINGS
###############################################################################

# Enable the following lines and install the browser extension to use Django debug toolbar
# if your deployment method is not VMWare of Docker-for-Mac you may
# need a different IP address from request.META['REMOTE_ADDR']
# INTERNAL_IPS = ('172.19.0.1', '172.18.0.1', '192.168.100.1')
# ALLOWED_HOSTS = ['*']

# The UUID of the system, for HA.
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'

# If set, use -vvv for project updates instead of -v for more output.
# PROJECT_UPDATE_VVV=True

###############################################################################
# LOGGING SETTINGS
###############################################################################

# Enable logging to syslog. Setting level to ERROR captures 500 errors,
# WARNING also logs 4xx responses.

# Enable the following lines to turn on lots of permissions-related logging.
# LOGGING['loggers']['awx.main.access']['level'] = 'DEBUG'
# LOGGING['loggers']['awx.main.signals']['level'] = 'DEBUG'
# LOGGING['loggers']['awx.main.permissions']['level'] = 'DEBUG'

# Enable the following line to turn on database settings logging.
# LOGGING['loggers']['awx.conf']['level'] = 'DEBUG'

# Enable the following lines to turn on LDAP auth logging.
# LOGGING['loggers']['django_auth_ldap']['handlers'] = ['console']
# LOGGING['loggers']['django_auth_ldap']['level'] = 'DEBUG'

BROADCAST_WEBSOCKET_PORT = 8013
BROADCAST_WEBSOCKET_VERIFY_CERT = False
BROADCAST_WEBSOCKET_PROTOCOL = 'http'
