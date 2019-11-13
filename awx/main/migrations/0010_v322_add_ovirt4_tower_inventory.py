# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# AWX
from awx.main.migrations import _migration_utils as migration_utils
from awx.main.migrations import _credentialtypes as credentialtypes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0009_v322_add_setting_field_for_activity_stream'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'File, Directory or Script'), ('scm', 'Sourced from a Project'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('rhv', 'Red Hat Virtualization'), ('tower', 'Ansible Tower'), ('custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'File, Directory or Script'), ('scm', 'Sourced from a Project'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('rhv', 'Red Hat Virtualization'), ('tower', 'Ansible Tower'), ('custom', 'Custom Script')]),
        ),
    ]
