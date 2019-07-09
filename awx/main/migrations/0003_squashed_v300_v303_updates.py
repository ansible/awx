# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import awx.main.fields

from . import _squashed
from ._squashed_30 import SQUASHED_30


class Migration(migrations.Migration):
    replaces = [('main', '0020_v300_labels_changes'),
                ('main', '0021_v300_activity_stream'),
                ('main', '0022_v300_adhoc_extravars'),
                ('main', '0023_v300_activity_stream_ordering'),
                ('main', '0024_v300_jobtemplate_allow_simul'),
                ('main', '0025_v300_update_rbac_parents'),
                ('main', '0026_v300_credential_unique'),
                ('main', '0027_v300_team_migrations'),
                ('main', '0028_v300_org_team_cascade')] + _squashed.replaces(SQUASHED_30, applied=True)

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0002_squashed_v300_release'),
    ]

    operations = [
        # Labels Changes
        migrations.RemoveField(
            model_name='job',
            name='labels',
        ),
        migrations.RemoveField(
            model_name='jobtemplate',
            name='labels',
        ),
        migrations.AddField(
            model_name='unifiedjob',
            name='labels',
            field=models.ManyToManyField(related_name='unifiedjob_labels', to='main.Label', blank=True),
        ),
        migrations.AddField(
            model_name='unifiedjobtemplate',
            name='labels',
            field=models.ManyToManyField(related_name='unifiedjobtemplate_labels', to='main.Label', blank=True),
        ),
        # Activity Stream
        migrations.AddField(
            model_name='activitystream',
            name='role',
            field=models.ManyToManyField(to='main.Role', blank=True),
        ),
        migrations.AlterModelOptions(
            name='activitystream',
            options={'ordering': ('pk',)},
        ),
        # Adhoc extra vars
        migrations.AddField(
            model_name='adhoccommand',
            name='extra_vars',
            field=models.TextField(default='', blank=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default='ssh', max_length=32, choices=[('ssh', 'Machine'), ('net', 'Network'), ('scm', 'Source Control'), ('aws', 'Amazon Web Services'), ('rax', 'Rackspace'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure Classic (deprecated)'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'Local File, Directory or Script'), ('rax', 'Rackspace Cloud Servers'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure Classic (deprecated)'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default='', max_length=32, blank=True, choices=[('', 'Manual'), ('file', 'Local File, Directory or Script'), ('rax', 'Rackspace Cloud Servers'), ('ec2', 'Amazon EC2'), ('gce', 'Google Compute Engine'), ('azure', 'Microsoft Azure Classic (deprecated)'), ('azure_rm', 'Microsoft Azure Resource Manager'), ('vmware', 'VMware vCenter'), ('satellite6', 'Red Hat Satellite 6'), ('cloudforms', 'Red Hat CloudForms'), ('openstack', 'OpenStack'), ('custom', 'Custom Script')]),
        ),
        # jobtemplate allow simul
        migrations.AddField(
            model_name='jobtemplate',
            name='allow_simultaneous',
            field=models.BooleanField(default=False),
        ),
        # RBAC update parents
        migrations.AlterField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['organization.admin_role', 'admin_role'], to='main.Role', null='True'),
        ),
        migrations.AlterField(
            model_name='team',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role='admin_role', to='main.Role', null='True'),
        ),
        migrations.AlterField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['organization.auditor_role', 'member_role'], to='main.Role', null='True'),
        ),
        # Unique credential
        migrations.AlterUniqueTogether(
            name='credential',
            unique_together=set([('organization', 'name', 'kind')]),
        ),
        migrations.AlterField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=['singleton:system_auditor', 'organization.auditor_role', 'use_role', 'admin_role'], to='main.Role', null='True'),
        ),
        # Team cascade
        migrations.AlterField(
            model_name='team',
            name='organization',
            field=models.ForeignKey(related_name='teams', on_delete=models.CASCADE, to='main.Organization'),
            preserve_default=False,
        ),
    ] + _squashed.operations(SQUASHED_30, applied=True)
