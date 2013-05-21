#!/usr/bin/env python

import os

if __name__ == '__main__':
    # Since this manage.py will only be used when running from a source
    # checkout, default to using the development settings.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lib.settings.development')
    from lib import manage
    manage()
