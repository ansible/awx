# -*- coding: utf-8 -*-
# Python
from __future__ import unicode_literals

# Psycopg2
from psycopg2.extensions import AsIs

# Django
from django.db import migrations, models

# AWX
import awx.main.fields
from awx.main.models import Host


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
            field=models.OneToOneField(related_name='deprecated_inventory_source', null=True, default=None, to='main.Group'),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='inventory',
            field=models.ForeignKey(related_name='inventory_sources', default=None, to='main.Inventory', null=True),
        ),

        # Facts
        migrations.AlterField(
            model_name='fact',
            name='facts',
            field=awx.main.fields.JSONBField(default={}, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True),
        ),
        migrations.AddField(
            model_name='host',
            name='ansible_facts',
            field=awx.main.fields.JSONBField(default={}, help_text='Arbitrary JSON structure of most recent ansible_facts, per-host.', blank=True),
        ),
        migrations.RunSQL([("CREATE INDEX host_ansible_facts_default_gin ON %s USING gin"
                            "(ansible_facts jsonb_path_ops);", [AsIs(Host._meta.db_table)])],
                          [('DROP INDEX host_ansible_facts_default_gin;', None)]),
    ]
