# Copyright (c) 2015 Ansible, Inc.
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
    context = getattr(request, 'parser_context', {})
    return {
        'version': get_awx_version(),
        'tower_version': get_awx_version(),
        'short_tower_version': get_awx_version().split('-')[0],
        'deprecated': getattr(
            context.get('view'),
            'deprecated',
            False
        )
    }
