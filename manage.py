#!/usr/bin/env python

# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import os

if __name__ == '__main__':
    # Since this manage.py will only be used when running from a source
    # checkout, default to using the development settings.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'ansibleworks.settings.development')
    from ansibleworks import manage
    manage()
