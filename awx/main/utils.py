# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import logging
import re
import subprocess
import sys

# Django REST Framework
from rest_framework.exceptions import ParseError, PermissionDenied

__all__ = ['get_object_or_400', 'get_object_or_403', 'camelcase_to_underscore',
           'get_ansible_version', 'get_awx_version']

def get_object_or_400(klass, *args, **kwargs):
    '''
    Return a single object from the given model or queryset based on the query
    params, otherwise raise an exception that will return in a 400 response.
    '''
    from django.shortcuts import _get_queryset
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist, e:
        raise ParseError(*e.args)
    except queryset.model.MultipleObjectsReturned, e:
        raise ParseError(*e.args)

def get_object_or_403(klass, *args, **kwargs):
    '''
    Return a single object from the given model or queryset based on the query
    params, otherwise raise an exception that will return in a 403 response.
    '''
    from django.shortcuts import _get_queryset
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist, e:
        raise PermissionDenied(*e.args)
    except queryset.model.MultipleObjectsReturned, e:
        raise PermissionDenied(*e.args)

def camelcase_to_underscore(s):
    '''
    Convert CamelCase names to lowercase_with_underscore.
    '''
    s = re.sub(r'(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', s)
    return s.lower().strip('_')

class RequireDebugTrueOrTest(logging.Filter):
    '''
    Logging filter to output when in DEBUG mode or running tests.
    '''

    def filter(self, record):
        from django.conf import settings
        return settings.DEBUG or 'test' in sys.argv

def get_ansible_version():
    '''
    Return Ansible version installed.
    '''
    try:
        proc = subprocess.Popen(['ansible', '--version'],
                                stdout=subprocess.PIPE)
        result = proc.communicate()[0]
        return result.lower().replace('ansible', '').strip()
    except:
        return 'unknown'

def get_awx_version():
    '''
    Return AWX version as reported by setuptools.
    '''
    from awx import __version__
    try:
        import pkg_resources
        return pkg_resources.require('awx')[0].version
    except:
        return __version__
