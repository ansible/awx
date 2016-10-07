# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0038_v310_workflow_rbac_prompts'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.CharField(unique=True, max_length=200)),
                ('channels', models.TextField()),
            ],
        ),
    ]
