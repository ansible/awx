# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0029_v302_add_ask_skip_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='teams',
            field=models.ManyToManyField(related_name='credentials', to='main.Team', blank=True),
        ),
        migrations.AddField(
            model_name='team',
            name='auditor_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'organization.auditor_role', to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_auditor', b'organization.auditor_role', b'teams.auditor_role', b'use_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'auditor_role', b'member_role'], to='main.Role', null=b'True'),
        ),
    ]
