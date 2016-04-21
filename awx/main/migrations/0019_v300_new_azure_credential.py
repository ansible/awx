# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_v300_host_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='credential',
            name='client',
            field=models.CharField(default=b'', help_text='Client Id or Application Id for the credential', max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='secret',
            field=models.CharField(default=b'', help_text='Secret Token for this credential', max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='subscription',
            field=models.CharField(default=b'', help_text='Subscription identifier for this credential', max_length=1024, blank=True),
        ),
        migrations.AddField(
            model_name='credential',
            name='tenant',
            field=models.CharField(default=b'', help_text='Tenant identifier for this credential', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default=b'ssh', max_length=32, choices=[(b'ssh', 'Machine'), (b'net', 'Network'), (b'scm', 'Source Control'), (b'aws', 'Amazon Web Services'), (b'rax', 'Rackspace'), (b'vmware', 'VMware vCenter'), (b'foreman', 'Satellite 6'), (b'cloudforms', 'CloudForms'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='host',
            name='instance_id',
            field=models.CharField(default=b'', max_length=1024, blank=True),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'foreman', 'Satellite 6'), (b'cloudforms', 'CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'foreman', 'Satellite 6'), (b'cloudforms', 'CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),

    ]
