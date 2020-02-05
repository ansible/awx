# -*- coding: utf-8 -*-
from uuid import uuid4

from django.db import migrations


def _generate_new_uuid_for_iso_nodes(apps, schema_editor):
    Instance = apps.get_model('main', 'Instance')
    for instance in Instance.objects.all():
        # The below code is a copy paste of instance.is_isolated()
        # We can't call is_isolated because we are using the "old" version
        # of the Instance definition.
        if instance.rampart_groups.filter(controller__isnull=False).exists():
            instance.uuid = str(uuid4())
            instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0100_v370_projectupdate_job_tags'),
    ]

    operations = [
        migrations.RunPython(_generate_new_uuid_for_iso_nodes)
    ]
