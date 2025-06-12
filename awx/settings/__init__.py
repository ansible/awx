# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import os
import copy
from ansible_base.lib.dynamic_config import (
    factory,
    export,
    load_envvars,
    load_python_file_with_injected_context,
    load_standard_settings_files,
    toggle_feature_flags,
)
from .functions import (
    assert_production_settings,
    merge_application_name,
    add_backwards_compatibility,
    load_extra_development_files,
)

add_backwards_compatibility()

# Create a the standard DYNACONF instance which will come with DAB defaults
# This loads defaults.py and environment specific file e.g: development_defaults.py
DYNACONF = factory(
    __name__,
    "AWX",
    environments=("development", "production", "quiet", "kube"),
    settings_files=["defaults.py"],
)

# Store snapshot before loading any custom config file
DYNACONF.set(
    "DEFAULTS_SNAPSHOT",
    copy.deepcopy(DYNACONF.as_dict(internal=False)),
    loader_identifier="awx.settings:DEFAULTS_SNAPSHOT",
)

#############################################################################################
# Settings loaded before this point will be allowed to be overridden by the database settings
# Any settings loaded after this point will be marked as as a read_only database setting
#############################################################################################

# Load extra settings files from the following directories
#  /etc/tower/conf.d/ and /etc/tower/
# this is the legacy location, kept for backwards compatibility
settings_dir = os.environ.get('AWX_SETTINGS_DIR', '/etc/tower/conf.d/')
settings_files_path = os.path.join(settings_dir, '*.py')
settings_file_path = os.environ.get('AWX_SETTINGS_FILE', '/etc/tower/settings.py')
load_python_file_with_injected_context(settings_files_path, settings=DYNACONF)
load_python_file_with_injected_context(settings_file_path, settings=DYNACONF)

# Load extra settings files from the following directories
# /etc/ansible-automation-platform/{settings,flags,.secrets}.yaml
# and /etc/ansible-automation-platform/awx/{settings,flags,.secrets}.yaml
# this is the new standard location for all services
load_standard_settings_files(DYNACONF)

# Load optional development only settings files
load_extra_development_files(DYNACONF)

# Check at least one setting file has been loaded in production mode
assert_production_settings(DYNACONF, settings_dir, settings_file_path)

# Load envvars at the end to allow them to override everything loaded so far
load_envvars(DYNACONF)

# This must run after all custom settings are loaded
DYNACONF.update(
    merge_application_name(DYNACONF),
    loader_identifier="awx.settings:merge_application_name",
    merge=True,
)

# Toggle feature flags based on installer settings
DYNACONF.update(
    toggle_feature_flags(DYNACONF),
    loader_identifier="awx.settings:toggle_feature_flags",
    merge=True,
)

# Update django.conf.settings with DYNACONF values
export(__name__, DYNACONF)
