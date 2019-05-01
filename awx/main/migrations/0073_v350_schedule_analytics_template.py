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

import jsonfield.fields
import jsonbfield.fields
import taggit.managers


def create_system_job_templates(apps, schema_editor):
    '''
    Create default system job templates if not present. Create default schedules
    only if new system job templates were created (i.e. new database).
    '''

    SystemJobTemplate = apps.get_model('main', 'SystemJobTemplate')
    Schedule = apps.get_model('main', 'Schedule')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    sjt_ct = ContentType.objects.get_for_model(SystemJobTemplate)
    now_dt = now()
    random_time = now() + timedelta(minutes=random.randint(-30,30))
    random_schedule_time = random_time.strftime('%Y%m%dT%H%M%SZ')

    sjt, created = SystemJobTemplate.objects.get_or_create(
        job_type='gather_analytics --ship',
        defaults=dict(
            name='Automation Insights Collection',
            description='Collect analytics data and send it to Automation Insights',
            created=now_dt,
            modified=now_dt,
            polymorphic_ctype=sjt_ct,
        ),
    )
    if created:
        sched = Schedule(
            name='Gather Automation Insights',
            rrule='DTSTART:%s RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1' % random_schedule_time,
            description='Automatically Generated Schedule',
            enabled=False,
            extra_data={},
            created=now_dt,
            modified=now_dt,
        )
        sched.unified_job_template = sjt
        sched.save()


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

