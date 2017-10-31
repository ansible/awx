# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorysource',
            name='plugin_path',
            field=models.CharField(default=b'', help_text='Inventory plugin to use for import, use leading @ to get from relative path in source control.', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source_path',
            field=models.CharField(default=b'', help_text='Relative path of inventory in source control.', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='plugin_path',
            field=models.CharField(default=b'', help_text='Inventory plugin to use for import, use leading @ to get from relative path in source control.', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source_path',
            field=models.CharField(default=b'', help_text='Relative path of inventory in source control.', max_length=1024, blank=True),
        ),
    ]
