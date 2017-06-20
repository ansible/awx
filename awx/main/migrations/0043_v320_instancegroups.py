# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0042_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstanceGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=250)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('controller', models.ForeignKey(related_name='controlled_groups', default=None, editable=False, to='main.InstanceGroup', help_text='Instance Group to remotely control this group.', null=True)),
                ('instances', models.ManyToManyField(help_text='Instances that are members of this InstanceGroup', related_name='rampart_groups', editable=False, to='main.Instance')),
            ],
        ),
        migrations.AddField(
            model_name='inventory',
            name='instance_groups',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='instance_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.InstanceGroup', help_text='The Rampart/Instance group the job was run under', null=True),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='instance_groups',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='instance_groups',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='activitystream',
            name='instance_group',
            field=models.ManyToManyField(to='main.InstanceGroup', blank=True),
        ),
        migrations.AddField(
            model_name='instance',
            name='last_isolated_check',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
