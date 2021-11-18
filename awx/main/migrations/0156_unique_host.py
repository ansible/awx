# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0155_improved_health_check'),
    ]

    operations = [
        migrations.CreateModel(
            name='UniqueHost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=None, editable=False)),
                ('modified', models.DateTimeField(default=None, editable=False)),
                ('host_name', models.CharField(default='', max_length=1024, editable=False)),
                (
                    'host',
                    models.ForeignKey(
                        related_name='unique_hosts', on_delete=django.db.models.deletion.SET_NULL, default=None, editable=False, to='main.Host', null=True
                    ),
                ),
                (
                    'job_host_summary',
                    models.ForeignKey(
                        related_name='unique_hosts',
                        on_delete=django.db.models.deletion.SET_NULL,
                        default=None,
                        editable=False,
                        to='main.JobHostSummary',
                        null=True,
                    ),
                ),
                ('recorded_date', models.DateTimeField(default=None, editable=False, null=True)),
            ],
            options={
                'ordering': ('-pk',),
                'verbose_name_plural': 'unique hosts',
            },
        ),
    ]
