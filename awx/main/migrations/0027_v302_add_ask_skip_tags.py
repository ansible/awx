# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import awx.main.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0026_v300_credential_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_skip_tags_on_launch',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_auditor', b'organization.auditor_role', b'use_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
    ]
