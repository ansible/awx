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
from awx.main.migrations._create_collection_system_jt import create_system_job_templates

import jsonfield.fields
import jsonbfield.fields
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0072_v350_deprecate_fields'),
    ]

    operations = [
        # Schedule Analytics System Job Template
        migrations.RunPython(create_system_job_templates, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='systemjob',
            name='job_type',
            field=models.CharField(blank=True, choices=[('cleanup_jobs', 'Remove jobs older than a certain number of days'), ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), ('cleanup_facts', 'Purge and/or reduce the granularity of system tracking data'), ('gather_analytics', 'Collects and sends Automation Insights data')], default='', max_length=32),
        ),
        migrations.AlterField(
            model_name='systemjobtemplate',
            name='job_type',
            field=models.CharField(blank=True, choices=[('cleanup_jobs', 'Remove jobs older than a certain number of days'), ('cleanup_activitystream', 'Remove activity stream entries older than a certain number of days'), ('cleanup_facts', 'Purge and/or reduce the granularity of system tracking data'), ('gather_analytics', 'Collects and sends Automation Insights data')], default='', max_length=32),
        ),
    ]

