# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

from awx.main.models.base import *
from awx.main.models.organization import *
from awx.main.models.projects import *
from awx.main.models.inventory import *
from awx.main.models.jobs import *

# Monkeypatch Django serializer to ignore django-taggit fields (which break
# the dumpdata command; see https://github.com/alex/django-taggit/issues/155).
from django.core.serializers.python import Serializer as _PythonSerializer
_original_handle_m2m_field = _PythonSerializer.handle_m2m_field
def _new_handle_m2m_field(self, obj, field):
    try:
        field.rel.through._meta
    except AttributeError:
        return
    return _original_handle_m2m_field(self, obj, field)
_PythonSerializer.handle_m2m_field = _new_handle_m2m_field

# Add custom methods to User model for permissions checks.
from django.contrib.auth.models import User
from awx.main.access import *
User.add_to_class('get_queryset', get_user_queryset)
User.add_to_class('can_access', check_user_access)

# Import signal handlers only after models have been defined.
import awx.main.signals
