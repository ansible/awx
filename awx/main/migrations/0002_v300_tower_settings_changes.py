# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TowerSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('key', models.CharField(unique=True, max_length=255)),
                ('description', models.TextField()),
                ('category', models.CharField(max_length=128)),
                ('value', models.TextField(blank=True)),
                ('value_type', models.CharField(max_length=12, choices=[(b'string', 'String'), (b'int', 'Integer'), (b'float', 'Decimal'), (b'json', 'JSON'), (b'bool', 'Boolean'), (b'password', 'Password'), (b'list', 'List')])),
                ('user', models.ForeignKey(related_name='settings', default=None, editable=False, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
