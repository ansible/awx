# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Django
from django.db import migrations, models

from psycopg2.extensions import AsIs

# AWX
import awx.main.fields
from awx.main.models import FactLatest


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0036_v311_insights'),
    ]

    operations = [
        # Inventory Refresh
        migrations.RenameField(
            'InventorySource',
            'group',
            'deprecated_group'
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='deprecated_group',
            field=models.ForeignKey(related_name='deprecated_inventory_source', default=None, null=True, to='main.Group'),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='inventory',
            field=models.ForeignKey(related_name='inventory_sources', default=None, to='main.Inventory', null=True),
        ),

        # Facts Latest
        migrations.CreateModel(
            name='FactLatest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=None, help_text='Date and time of the corresponding fact scan gathering time.', editable=False)),
                ('module', models.CharField(max_length=128)),
                ('facts', awx.main.fields.JSONBField(default={}, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True)),
                ('host', models.ForeignKey(related_name='facts_latest', to='main.Host', help_text='Host for the facts that the fact scan captured.')),
            ],
        ),
        migrations.AlterField(
            model_name='fact',
            name='facts',
            field=awx.main.fields.JSONBField(default={}, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True),
        ),
        migrations.AlterIndexTogether(
            name='factlatest',
            index_together=set([('timestamp', 'module', 'host')]),
        ),
        migrations.RunSQL([("CREATE INDEX fact_latest_facts_default_gin ON %s USING gin"
                            "(facts jsonb_path_ops);", [AsIs(FactLatest._meta.db_table)])],
                          [('DROP INDEX fact_latest_facts_default_gin;', None)]),
    ]
