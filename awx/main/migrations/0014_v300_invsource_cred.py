# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_v300_label_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='network_credential',
            field=models.ForeignKey(related_name='jobs_as_network_credential+', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AddField(
            model_name='jobtemplate',
            name='network_credential',
            field=models.ForeignKey(related_name='jobtemplates_as_network_credential+', on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='main.Credential', null=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='deprecated_team',
            field=models.ForeignKey(related_name='deprecated_credentials', default=None, blank=True, to='main.Team', null=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='deprecated_user',
            field=models.ForeignKey(related_name='deprecated_credentials', default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default=b'ssh', max_length=32, choices=[(b'ssh', 'Machine'), (b'net', 'Network'), (b'scm', 'Source Control'), (b'aws', 'Amazon Web Services'), (b'rax', 'Rackspace'), (b'vmware', 'VMware vCenter'), (b'foreman', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure'), (b'openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure'), (b'vmware', 'VMware vCenter'), (b'foreman', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure'), (b'vmware', 'VMware vCenter'), (b'foreman', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='team',
            name='deprecated_projects',
            field=models.ManyToManyField(related_name='deprecated_teams', to='main.Project', blank=True),
        ),
    ]
