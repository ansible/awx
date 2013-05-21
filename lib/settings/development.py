# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Development settings for Ansible Commander project.

from defaults import *

# If a local_settings.py file is present here, use it and ignore the global
# settings.  Normally local settings would only be present during development.
try:
    local_settings_file = os.path.join(os.path.dirname(__file__),
                                       'local_settings.py')
    execfile(local_settings_file)
    # Hack so that the autoreload will detect changes to local_settings.py.
    class dummymodule(str):
        __file__ = property(lambda self: self)
    sys.modules['local_settings'] = dummymodule(local_settings_file)
except IOError:
    # Otherwise, rely on the global settings file specified in the environment,
    # defaulting to /etc/ansibleworks/settings.py.
    try:
        settings_file = os.environ.get('ANSIBLEWORKS_SETTINGS_FILE',
                                       '/etc/ansibleworks/settings.py')
        execfile(settings_file)
    except IOError:
        pass
