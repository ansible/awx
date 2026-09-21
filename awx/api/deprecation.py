# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""
Deprecation header mechanism for AWX API endpoints.

Based on the Controller POC (ANSTRAT-2346).

Imports deprecation utilities from django-ansible-base.
"""

from ansible_base.lib.utils.views.deprecation import deprecated, mark_deprecated

__all__ = ['deprecated', 'mark_deprecated']
