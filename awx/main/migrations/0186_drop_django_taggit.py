# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from ._sqlite_helper import dbawaremigrations


def delete_taggit_contenttypes(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.filter(app_label='taggit').delete()


def delete_taggit_migration_records(apps, schema_editor):
    recorder = migrations.recorder.MigrationRecorder(connection=schema_editor.connection)
    recorder.migration_qs.filter(app='taggit').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0185_move_JSONBlob_to_JSONField'),
    ]

    operations = [
        dbawaremigrations.RunSQL("DROP TABLE IF EXISTS taggit_tag CASCADE;", sqlite_sql="DROP TABLE IF EXISTS taggit_tag;"),
        dbawaremigrations.RunSQL("DROP TABLE IF EXISTS taggit_taggeditem CASCADE;", sqlite_sql="DROP TABLE IF EXISTS taggit_taggeditem;"),
        migrations.RunPython(delete_taggit_contenttypes),
        migrations.RunPython(delete_taggit_migration_records),
    ]
