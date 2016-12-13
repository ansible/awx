# -*- coding: utf-8 -*-

# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import awx.main.fields
import jsonfield.fields


def update_dashed_host_variables(apps, schema_editor):
    Host = apps.get_model('main', 'Host')
    for host in Host.objects.filter(variables='---'):
        host.variables = ''
        host.save()


class Migration(migrations.Migration):
    replaces = [(b'main', '0020_v300_labels_changes'),
                (b'main', '0021_v300_activity_stream'),
                (b'main', '0022_v300_adhoc_extravars'),
                (b'main', '0023_v300_activity_stream_ordering'),
                (b'main', '0024_v300_jobtemplate_allow_simul'),
                (b'main', '0025_v300_update_rbac_parents'),
                (b'main', '0026_v300_credential_unique'),
                (b'main', '0027_v300_team_migrations'),
                (b'main', '0028_v300_org_team_cascade'),
                (b'main', '0029_v302_add_ask_skip_tags'),
                (b'main', '0030_v302_job_survey_passwords'),
                (b'main', '0031_v302_migrate_survey_passwords'),
                (b'main', '0032_v302_credential_permissions_update'),
                (b'main', '0033_v303_v245_host_variable_fix'),]


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
        # add ask skip tags
        migrations.AddField(
            model_name='jobtemplate',
            name='ask_skip_tags_on_launch',
            field=models.BooleanField(default=False),
        ),
        # job survery passwords
        migrations.AddField(
            model_name='job',
            name='survey_passwords',
            field=jsonfield.fields.JSONField(default={}, editable=False, blank=True),
        ),
        # RBAC credential permission updates
        migrations.AlterField(
            model_name='credential',
            name='admin_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'singleton:system_administrator', b'organization.admin_role'], to='main.Role', null=b'True'),
        ),
        migrations.AlterField(
            model_name='credential',
            name='use_role',
            field=awx.main.fields.ImplicitRoleField(related_name='+', parent_role=[b'admin_role'], to='main.Role', null=b'True'),
        ),
    ]
