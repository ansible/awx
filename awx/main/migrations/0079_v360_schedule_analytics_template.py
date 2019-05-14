# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from __future__ import unicode_literals
import random
import awx.main.fields

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils.timezone import now, timedelta
from awx.main.migrations._create_system_jobs import create_collection_jt

import jsonfield.fields
import jsonbfield.fields
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0078_v360_clear_sessions_tokens_jt'),
    ]

    operations = [
        # Schedule Analytics System Job Template
        migrations.RunPython(create_collection_jt, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='systemjob',
            name='job_type',
            field=models.CharField(blank=True, choices=[('cleanup_jobs', 'Remove jobs older than a certain number of days'), ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), ('cleanup_facts', 'Purge and/or reduce the granularity of system tracking data'), ('clearsessions', 'Removes expired browser sessions from the database'), ('cleartokens', 'Removes expired OAuth 2 access tokens and refresh tokens'), ('gather_analytics', 'Collects and sends Automation Insights data')], default='', max_length=32),
        ),
        migrations.AlterField(
            model_name='systemjobtemplate',
            name='job_type',
            field=models.CharField(blank=True, choices=[('cleanup_jobs', 'Remove jobs older than a certain number of days'), ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), ('cleanup_facts', 'Purge and/or reduce the granularity of system tracking data'), ('clearsessions', 'Removes expired browser sessions from the database'), ('cleartokens', 'Removes expired OAuth 2 access tokens and refresh tokens'), ('gather_analytics', 'Collects and sends Automation Insights data')], default='', max_length=32),
        ),
    ]
