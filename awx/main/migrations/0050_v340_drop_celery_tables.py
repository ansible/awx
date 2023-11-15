# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from ._sqlite_helper import dbawaremigrations

tables_to_drop = [
    'celery_taskmeta',
    'celery_tasksetmeta',
    'djcelery_crontabschedule',
    'djcelery_intervalschedule',
    'djcelery_periodictask',
    'djcelery_periodictasks',
    'djcelery_taskstate',
    'djcelery_workerstate',
    'djkombu_message',
    'djkombu_queue',
]
postgres_sql = ([("DROP TABLE IF EXISTS {} CASCADE;".format(table))] for table in tables_to_drop)
sqlite_sql = ([("DROP TABLE IF EXISTS {};".format(table))] for table in tables_to_drop)


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0049_v330_validate_instance_capacity_adjustment'),
    ]

    operations = [dbawaremigrations.RunSQL(p, sqlite_sql=s) for p, s in zip(postgres_sql, sqlite_sql)]
