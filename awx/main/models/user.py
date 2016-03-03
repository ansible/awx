# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from awx.main.models.base import CommonModelNameNotUnique
from awx.main.models.mixins import ResourceMixin
from awx.main.fields import AutoOneToOneField, ImplicitRoleField


class UserResource(CommonModelNameNotUnique, ResourceMixin):
    class Meta:
        app_label = 'main'
        verbose_name = _('user_resource')
        verbose_name_plural = _('user_resources')
        unique_together = [('user', 'admin_role'),]
        db_table = 'main_rbac_user_resource'

    user = AutoOneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='resource',
        editable=False,
    )

    admin_role = ImplicitRoleField(
        role_name='User Administrator',
        role_description='May manage this user',
        permissions = {'all': True},
    )
