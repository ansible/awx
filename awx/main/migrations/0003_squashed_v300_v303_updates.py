# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import awx.main.fields

import _squashed
from _squashed_300 import SQUASHED_300


class Migration(migrations.Migration):
    replaces = [(b'main', '0020_v300_labels_changes'),
                (b'main', '0021_v300_activity_stream'),
                (b'main', '0022_v300_adhoc_extravars'),
                (b'main', '0023_v300_activity_stream_ordering'),
                (b'main', '0024_v300_jobtemplate_allow_simul'),
                (b'main', '0025_v300_update_rbac_parents'),
                (b'main', '0026_v300_credential_unique'),
                (b'main', '0027_v300_team_migrations'),
                (b'main', '0028_v300_org_team_cascade')] + _squashed.replaces(SQUASHED_300)


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
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='credential',
            name='kind',
            field=models.CharField(default=b'ssh', max_length=32, choices=[(b'ssh', 'Machine'), (b'net', 'Network'), (b'scm', 'Source Control'), (b'aws', 'Amazon Web Services'), (b'rax', 'Rackspace'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'openstack', 'OpenStack')]),
        ),
        migrations.AlterField(
            model_name='inventorysource',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
        ),
        migrations.AlterField(
            model_name='inventoryupdate',
            name='source',
            field=models.CharField(default=b'', max_length=32, blank=True, choices=[(b'', 'Manual'), (b'file', 'Local File, Directory or Script'), (b'rax', 'Rackspace Cloud Servers'), (b'ec2', 'Amazon EC2'), (b'gce', 'Google Compute Engine'), (b'azure', 'Microsoft Azure Classic (deprecated)'), (b'azure_rm', 'Microsoft Azure Resource Manager'), (b'vmware', 'VMware vCenter'), (b'satellite6', 'Red Hat Satellite 6'), (b'cloudforms', 'Red Hat CloudForms'), (b'openstack', 'OpenStack'), (b'custom', 'Custom Script')]),
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
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.admin_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='team',
            name='member_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=b'admin_role', to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='team',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'organization.auditor_role', b'member_role'], to='main.Role', null=b'True'),
        ),
        # Unique credential
        migrations.AlterUniqueTogether(
            name='credential',
            unique_together=set([('organization', 'name', 'kind')]),
        ),
        migrations.AlterField(
            model_name='credential',
            name='read_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_auditor', b'organization.auditor_role', b'use_role', b'admin_role'], to='main.Role', null=b'True'),
        ),
        # Team cascade
        migrations.AlterField(
            model_name='team',
            name='organization',
            field=models.ForeignKey(related_name='teams', to='main.Organization'),
            preserve_default=False,
        ),
    ] + _squashed.operations(SQUASHED_300)
