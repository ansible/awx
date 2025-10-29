# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Development settings for AWX project.

# Python
import os
import socket

# Centos-7 doesn't include the svg mime type
# /usr/lib64/python/mimetypes.py
import mimetypes

from dynaconf import post_hook

# awx-manage shell_plus --notebook
NOTEBOOK_ARGUMENTS = ['--NotebookApp.token=', '--ip', '0.0.0.0', '--port', '9888', '--allow-root', '--no-browser']

# print SQL queries in shell_plus
SHELL_PLUS_PRINT_SQL = False

# show colored logs in the dev environment
# to disable this, set `COLOR_LOGS = False` in awx/settings/local_settings.py
COLOR_LOGS = True
LOGGING__handlers__console = '@merge {"()": "awx.main.utils.handlers.ColorHandler"}'

ALLOWED_HOSTS = ['*']

mimetypes.add_type("image/svg+xml", ".svg", True)
mimetypes.add_type("image/svg+xml", ".svgz", True)

# Disallow sending session cookies over insecure connections
SESSION_COOKIE_SECURE = False

# Disallow sending csrf cookies over insecure connections
CSRF_COOKIE_SECURE = False

# Disable Pendo on the UI for development/test.
# Note: This setting may be overridden by database settings.
PENDO_TRACKING_STATE = "off"
INSIGHTS_TRACKING_STATE = False

# debug toolbar and swagger assume that requirements/requirements_dev.txt are installed
INSTALLED_APPS = "@merge drf_spectacular,debug_toolbar"
MIDDLEWARE = "@insert 0 debug_toolbar.middleware.DebugToolbarMiddleware"

DEBUG_TOOLBAR_CONFIG = {'ENABLE_STACKTRACES': True}

# drf-spectacular settings for API schema generation
SPECTACULAR_SETTINGS = {
    'TITLE': 'AWX API',
    'DESCRIPTION': 'AWX API Documentation',
    'VERSION': 'v2',
    'OAS_VERSION': '3.0.3',  # Set OpenAPI Specification version to 3.0.3
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': r'/api/v[0-9]',
    'DEFAULT_GENERATOR_CLASS': 'drf_spectacular.generators.SchemaGenerator',
    'SCHEMA_COERCE_PATH_PK_SUFFIX': True,
    'CONTACT': {'email': 'contact@snippets.local'},
    'LICENSE': {'name': 'Apache License'},
    'TERMS_OF_SERVICE': 'https://www.google.com/policies/terms/',
    # Use our custom schema class that handles swagger_topic and deprecated views
    'DEFAULT_SCHEMA_CLASS': 'awx.api.schema.CustomAutoSchema',
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
}

# Configure a default UUID for development only.
SYSTEM_UUID = '00000000-0000-0000-0000-000000000000'
INSTALL_UUID = '00000000-0000-0000-0000-000000000000'

# Ansible base virtualenv paths and enablement
# only used for deprecated fields and management commands for them
BASE_VENV_PATH = os.path.realpath("/var/lib/awx/venv")

CLUSTER_HOST_ID = socket.gethostname()

AWX_CALLBACK_PROFILE = True

# ======================!!!!!!! FOR DEVELOPMENT ONLY !!!!!!!=================================
# Disable normal scheduled/triggered task managers (DependencyManager, TaskManager, WorkflowManager).
# Allows user to trigger task managers directly for debugging and profiling purposes.
# Only works in combination with settings.SETTINGS_MODULE == 'awx.settings.development'
AWX_DISABLE_TASK_MANAGERS = False

# Needed for launching runserver in debug mode
# ======================!!!!!!! FOR DEVELOPMENT ONLY !!!!!!!=================================


# This modifies FLAGS set by defaults, must be deferred to run later
@post_hook
def set_dev_flags(settings):
    defaults_flags = settings.get("FLAGS", {})
    defaults_flags['FEATURE_INDIRECT_NODE_COUNTING_ENABLED'] = [{'condition': 'boolean', 'value': True}]
    defaults_flags['FEATURE_DISPATCHERD_ENABLED'] = [{'condition': 'boolean', 'value': True}]
    return {'FLAGS': defaults_flags}
