# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_v320_drop_v1_credential_fields'),
    ]

    operations = [
        migrations.RunPython(credentialtypes.create_ovirt4_credtype),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'File, Directory or Script'), (b'scm', 'Sourced from a Project'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'ovirt4', 'oVirt4'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'File, Directory or Script'), (b'scm', 'Sourced from a Project'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'ovirt4', 'oVirt4'), (b'custom', 'Custom Script')]),
        ),
    ]
