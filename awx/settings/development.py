# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Development settings for AWX project.

from defaults import *

# If a local_settings.py file is present in awx/settings/, use it to override
# default settings for development.  If not present, we can still run using
# the defaults.
try:
    local_settings_file = os.path.join(os.path.dirname(__file__),
                                       'local_settings.py')
    execfile(local_settings_file)
    # Hack so that the autoreload will detect changes to local_settings.py.
    class dummymodule(str):
        __file__ = property(lambda self: self)
    sys.modules['local_settings'] = dummymodule(local_settings_file)
except IOError, e:
    from django.core.exceptions import ImproperlyConfigured
    if os.path.exists(settings_file):
        msg = 'Unable to load %s: %s' % (local_settings_file, str(e))
        raise ImproperlyConfigured(msg)
