# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Django
from django.conf import settings as django_settings

# Ansible Tower
from awx.main.utils import get_awx_version

def settings(request):
    return {
        'settings': django_settings,
    }

def version(request):
    return {
        'version': get_awx_version(),
    }
