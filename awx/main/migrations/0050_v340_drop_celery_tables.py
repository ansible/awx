# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0049_v330_validate_instance_capacity_adjustment'),
    ]

    operations = [
        migrations.RunSQL([
            ("DROP TABLE IF EXISTS {} CASCADE;".format(table))
        ])
        for table in ('celery_taskmeta', 'celery_tasksetmeta', 'djcelery_crontabschedule',
                      'djcelery_intervalschedule', 'djcelery_periodictask',
                      'djcelery_periodictasks', 'djcelery_taskstate', 'djcelery_workerstate',
                      'djkombu_message', 'djkombu_queue')
    ]
