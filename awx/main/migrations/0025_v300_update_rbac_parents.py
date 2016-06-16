# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0024_v300_jobtemplate_allow_simul'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.admin_role', b'owner_role'], to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='team',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role', b'member_role'], to='main.Role', null=b'True'),
        ),
    ]
