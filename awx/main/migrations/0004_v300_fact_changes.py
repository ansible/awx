# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonbfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_v300_notification_changes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=None, help_text='Date and time of the corresponding fact scan gathering time.', editable=False)),
                ('module', models.CharField(max_length=128)),
                ('facts', jsonbfield.fields.JSONField(default={}, help_text='Arbitrary JSON structure of module facts captured at timestamp for a single host.', blank=True)),
                ('host', models.ForeignKey(related_name='facts', to='main.Host', help_text='Host for the facts that the fact scan captured.')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='fact',
            index_together=set([('timestamp', 'module', 'host')]),
        ),
    ]
