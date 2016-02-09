# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonbfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_v300_changes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(default=None, editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('module', models.CharField(max_length=128)),
                ('facts', jsonbfield.fields.JSONField(default={}, blank=True)),
                ('host', models.ForeignKey(related_name='facts', to='main.Host')),
            ],
        ),
        migrations.AlterIndexTogether(
            name='fact',
            index_together=set([('timestamp', 'module', 'host')]),
        ),
    ]
